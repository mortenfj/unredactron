#!/usr/bin/env python3
"""
Unredactron - PDF Redaction Forensic Analyzer
Uses width analysis + CSV candidate database to identify redacted text

Now with automated typographic profiling for font detection!
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import ImageFont
import csv
import sys
import argparse

# Import the font profiler
from font_profiler import FontProfiler

# Configuration
FILE_PATH = "files/EFTA00037366.pdf"
FONT_PATH = "fonts/fonts/times.ttf"
CANDIDATES_CSV = "candidates.csv"
OUTPUT_DIR = "analysis_output"

def load_candidates(csv_path):
    """Load candidates from simple CSV format"""
    candidates = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get('name', '').strip()
                if not name or name.startswith('#'):  # Skip empty lines and comments
                    continue

                confidence = float(row.get('confidence', 0)) if row.get('confidence') else 0
                notes = row.get('notes', '')

                candidates.append({
                    'name': name,
                    'confidence': confidence,
                    'notes': notes
                })

        # Sort by confidence (highest first)
        candidates.sort(key=lambda x: x['confidence'], reverse=True)
        return candidates

    except FileNotFoundError:
        print(f"Warning: {csv_path} not found. Using empty candidate list.")
        return []

def analyze_pdf(file_path, font_path, candidates, dpi=1200, font_profile=None):
    """Analyze PDF redactions against candidates

    Args:
        file_path: Path to PDF file
        font_path: Path to font file (fallback if no profile)
        candidates: List of candidate names
        dpi: Document DPI
        font_profile: Optional FontProfile object with auto-detected settings
    """

    print("="*100)
    print(f"UNREDACTRON - PDF Forensic Redaction Analyzer")
    print("="*100)

    # Load PDF
    print(f"\nLoading PDF: {file_path}")
    print(f"Resolution: {dpi} DPI")
    images = convert_from_path(file_path, dpi=dpi)
    img = np.array(images[0])
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

    # Load font (use profile if available, otherwise fallback)
    if font_profile:
        font_size = int(font_profile.font_size)
        font = ImageFont.truetype(font_profile.font_path, font_size)
        scale_factor = font_profile.scale_factor
        tracking_offset = font_profile.tracking_offset
        print(f"Using auto-detected font: {font_profile.font_name}")
        print(f"Font size: {font_size}pt, Scale factor: {scale_factor:.4f}, Tracking: {tracking_offset:+.2f}px")
    else:
        font_size = int(12 * dpi / 72)
        font = ImageFont.truetype(font_path, font_size)
        scale_factor = dpi / 72  # Basic DPI scaling
        tracking_offset = 0
        print(f"Using fallback font: {font_path}")

    # Find redactions
    print(f"Detecting redactions...")
    _, black_mask = cv2.threshold(gray, 5, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    redactions = [(x, y, w, h) for cnt in contours
                  for x, y, w, h in [cv2.boundingRect(cnt)]
                  if w > 200 and h > 100]

    print(f"Found {len(redactions)} significant redactions")
    print(f"Testing {len(candidates)} candidates")

    # Analyze each redaction
    results = []
    for i, (x, y, w, h) in enumerate(redactions):
        best_match = None
        best_error = 100

        for candidate in candidates:
            name = candidate['name']
            confidence = candidate['confidence']

            # Calculate expected width with calibration
            base_width = font.getlength(name)
            expected_width = base_width * scale_factor + (len(name) * tracking_offset)
            diff = abs(expected_width - w)
            pct_error = diff / expected_width * 100 if expected_width > 0 else 100

            # Combined score: width error - (confidence / 10)
            # Confidence acts as tie-breaker
            combined_score = pct_error - (confidence / 10)

            if combined_score < best_error:
                best_error = combined_score
                best_match = {
                    'redaction_id': i,
                    'position': (x, y),
                    'size': (w, h),
                    'candidate': name,
                    'confidence': confidence,
                    'expected_width': expected_width,
                    'actual_width': w,
                    'diff': diff,
                    'pct_error': pct_error,
                    'notes': candidate['notes']
                }

        if best_match and best_match['pct_error'] < 30:
            results.append(best_match)

    # Sort by error percentage
    results.sort(key=lambda r: r['pct_error'])

    return results, gray.shape

def display_results(results, image_shape, font_profile=None):
    """Display analysis results

    Args:
        results: List of match results
        image_shape: Shape of the analyzed image
        font_profile: Optional FontProfile object to display
    """

    if font_profile:
        print(f"\n{'='*100}")
        print("FORENSIC DOCUMENT PROFILE")
        print(f"{'='*100}")
        print(f"  Detected Font:     {font_profile.font_name}")
        print(f"  Font Size:         {font_profile.font_size:.1f} pt")
        print(f"  Tracking Offset:   {font_profile.tracking_offset:+.2f} px")
        print(f"  Kerning Mode:      {font_profile.kerning_mode}")
        print(f"  Scale Factor:      {font_profile.scale_factor:.4f}")
        print(f"  Confidence:        {font_profile.confidence:.1f}%")
        print(f"  Reference:         '{font_profile.reference_word}' "
              f"({font_profile.reference_width:.1f}px)")
        print(f"  Accuracy Score:    {font_profile.calibration_accuracy:.2f}%")
        print(f"{'='*100}\n")

    if not results:
        print("\nNo matches found!")
        return

    print(f"\n{'='*100}")
    print(f"DETECTED REDACTIONS - {len(results)} matches found")
    print(f"{'='*100}")

    print(f"\n{'Rank':<6} {'Detected Name':<30} {'Position':<18} {'Size':<12} "
          f"{'Width':<12} {'Diff':<10} {'Error':<8} {'Conf':<6}")
    print("-"*130)

    for i, match in enumerate(results[:20], 1):
        pos_str = f"({match['position'][0]}, {match['position'][1]})"
        size_str = f"{match['size'][0]}x{match['size'][1]}"

        # Confidence display
        conf_display = '+' * int(match['confidence']) if match['confidence'] >= 1 else ''

        # Rating
        if match['pct_error'] < 1:
            rating = "★★★"
        elif match['pct_error'] < 5:
            rating = "★★"
        elif match['pct_error'] < 10:
            rating = "★"
        else:
            rating = ""

        print(f"{i:<6} {match['candidate']:<30} {pos_str:<18} {size_str:<12} "
              f"{match['expected_width']:>8.1f}px  {match['diff']:>6.1f}px   "
              f"{match['pct_error']:>5.1f}%   {conf_display:<5} {rating}")

    # Statistics
    perfect = sum(1 for r in results if r['pct_error'] < 1)
    excellent = sum(1 for r in results if r['pct_error'] < 5)
    good = sum(1 for r in results if r['pct_error'] < 10)

    print(f"\n{'='*100}")
    print(f"STATISTICS:")
    print(f"  Total matches: {len(results)}")
    print(f"  Perfect (<1%): {perfect}")
    print(f"  Excellent (<5%): {excellent}")
    print(f"  Good (<10%): {good}")
    print(f"{'='*100}")

    # Show notes for top matches
    print(f"\nTOP 5 - WITH NOTES:")
    for i, match in enumerate(results[:5], 1):
        print(f"\n{i}. {match['candidate']} ({match['pct_error']:.1f}% error)")
        if match['notes']:
            print(f"   Note: {match['notes']}")

def main():
    """Main entry point"""

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Unredactron - PDF Redaction Forensic Analyzer')
    parser.add_argument('--file', type=str, default=FILE_PATH, help='Path to PDF file')
    parser.add_argument('--font', type=str, default=FONT_PATH, help='Path to font file (fallback)')
    parser.add_argument('--csv', type=str, default=CANDIDATES_CSV, help='Path to candidates CSV')
    parser.add_argument('--dpi', type=int, default=1200, help='Document DPI')
    parser.add_argument('--no-profile', action='store_true', help='Skip automatic font profiling')
    parser.add_argument('--save-profile', type=str, help='Save detected profile to file')
    args = parser.parse_args()

    # Step 1: Automatic Font Profiling (unless disabled)
    font_profile = None
    if not args.no_profile:
        print("\n" + "="*100)
        print("STEP 1: AUTOMATIC FONT DETECTION")
        print("="*100)

        profiler = FontProfiler(fonts_dir="fonts/fonts/")
        font_profile = profiler.profile_from_pdf(args.file, dpi=args.dpi, verbose=True)

        if font_profile and args.save_profile:
            profiler.save_profile(font_profile, args.save_profile)

        if not font_profile:
            print("\n[!] Font profiling failed, falling back to manual settings")
            print(f"[!] Using font: {args.font}")

    # Load candidates
    print(f"\n{'='*100}")
    print("STEP 2: CANDIDATE LOADING")
    print(f"{'='*100}")
    print(f"Loading candidates from: {args.csv}")
    candidates = load_candidates(args.csv)

    if not candidates:
        print("Warning: No candidates loaded!")
        return

    print(f"Loaded {len(candidates)} candidates")

    # Show top 10 by confidence
    print(f"\nTop 10 candidates by confidence:")
    for i, c in enumerate(candidates[:10], 1):
        conf_mark = '+' * int(c['confidence']) if c['confidence'] >= 1 else ''
        print(f"  {i:2d}. {c['name']:<30} confidence: {c['confidence']:4.1f} {conf_mark}")

    # Analyze PDF
    print(f"\n{'='*100}")
    print("STEP 3: REDACTION ANALYSIS")
    print(f"{'='*100}")
    results, image_shape = analyze_pdf(args.file, args.font, candidates, args.dpi, font_profile)

    # Display results
    display_results(results, image_shape, font_profile)

if __name__ == "__main__":
    main()
