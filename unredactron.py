#!/usr/bin/env python3
"""
Unredactron - PDF Redaction Forensic Analyzer
Uses width analysis + CSV candidate database to identify redacted text
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import ImageFont
import csv
import sys

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

def analyze_pdf(file_path, font_path, candidates, dpi=1200):
    """Analyze PDF redactions against candidates"""

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

    # Load font
    font_size = int(12 * dpi / 72)
    font = ImageFont.truetype(font_path, font_size)

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

            # Calculate expected width
            expected_width = font.getlength(name)
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

def display_results(results, image_shape):
    """Display analysis results"""

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

    # Load candidates
    print(f"Loading candidates from: {CANDIDATES_CSV}")
    candidates = load_candidates(CANDIDATES_CSV)

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
    results, image_shape = analyze_pdf(FILE_PATH, FONT_PATH, candidates)

    # Display results
    display_results(results, image_shape)

if __name__ == "__main__":
    main()
