#!/usr/bin/env python3
"""
Solve Redactions - "One-Click" Master Script

This script consolidates all individual tools into a single, high-level
command-line interface for identifying, verifying, and documenting redactions.

Usage:
    python solve_redactions.py --pdf files/document.pdf --candidates candidates.csv

Author: Unredactron Master Module
"""

import argparse
import sys
import os
import pandas as pd
from typing import List, Dict, Optional
from pdf2image import convert_from_path
import cv2
import numpy as np
from contextlib import redirect_stdout, suppress
import io

# Add helpers to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'helpers'))

from helpers.detect_font_v2 import detect_best_font
from helpers.unredactron_forensic import ForensicRedactionAnalyzer
from helpers.letter_reconstruction import verify_artifact_pattern
from helpers.generate_evidence_card import EvidenceCardGenerator


def load_candidates(csv_path: str) -> List[Dict]:
    """Load candidates from CSV file."""
    df = pd.read_csv(csv_path)
    return df.to_dict('records')


def run_master_analysis(
    pdf_path: str,
    candidates: List[Dict],
    dpi: int = 600,
    confidence_threshold: float = 90.0,
    evidence_output_dir: str = "solved_evidence",
    report_path: str = "solution_report.txt"
) -> Dict:
    """
    Run the complete redaction analysis pipeline.

    Args:
        pdf_path: Path to PDF document
        candidates: List of candidate dictionaries
        dpi: DPI for PDF conversion
        confidence_threshold: Minimum confidence for verification
        evidence_output_dir: Directory for evidence cards
        report_path: Path to solution report

    Returns:
        Dictionary with analysis results
    """
    results = {
        'pdf_path': pdf_path,
        'matches': [],
        'verified_matches': []
    }

    # ========================================================================
    # PHASE A: AUTO-CALIBRATION
    # ========================================================================
    print(f"[*] Analyzing {pdf_path}...")

    # Suppress verbose output from font detection
    null_fd = io.StringIO()
    with redirect_stdout(null_fd):
        font_profile = detect_best_font(pdf_path, verbose=False)

    if font_profile is None:
        print("[!] Font detection failed, using fallback: times.ttf")
        font_path = "fonts/fonts/times.ttf"
        font_size = 12
        scale_factor = dpi / 72
    else:
        font_path = font_profile['font_path']
        font_size = font_profile['font_size']
        scale_factor = font_profile['scale_factor']

    print(f"[+] Detected Profile: {os.path.basename(font_path)} @ {font_size}pt (Scale: {scale_factor:.2f})")

    # ========================================================================
    # PHASE B: FORENSIC SOLVER
    # ========================================================================
    print("\n[*] Running forensic solver with Dynamic Tolerance...")

    # Initialize forensic analyzer
    analyzer = ForensicRedactionAnalyzer(
        file_path=pdf_path,
        font_path=font_path,
        dpi=dpi,
        diagnostic_mode=False,  # Don't generate diagnostic sheets
        tolerance=3.0  # Dynamic tolerance is used internally
    )

    # Find redactions
    redactions = analyzer.find_redactions()

    # Match candidates (suppress verbose output)
    null_fd = io.StringIO()
    with redirect_stdout(null_fd):
        matches = analyzer.match_candidates_to_redactions(
            candidates=candidates,
            redactions=redactions,
            scale_factor=scale_factor
        )

    # Filter for high-confidence matches (>90%)
    high_confidence_matches = [
        m for m in matches
        if m['score'] > confidence_threshold
    ]

    print(f"[+] Found {len(high_confidence_matches)} high-confidence matches (>{confidence_threshold}%)")
    results['matches'] = high_confidence_matches

    if not high_confidence_matches:
        print("\n[!] No high-confidence matches found. Analysis complete.")
        return results

    # ========================================================================
    # PHASE C: DEEP VERIFICATION (The "DNA Check")
    # ========================================================================
    print("\n[*] Running deep artifact verification...")

    verified_matches = []

    for match in high_confidence_matches:
        redaction_idx = match['redaction_idx']
        candidate_name = match['name']
        redaction_coords = match['redaction_coords']

        print(f"\n[*] Verifying: {candidate_name} (Redaction #{redaction_idx + 1})")

        # Run artifact verification
        verification_result = verify_artifact_pattern(
            gray_image=analyzer.gray,
            redaction=redaction_coords,
            candidate_string=candidate_name,
            font_path=font_path,
            font_size=font_size,
            dpi=dpi,
            artifact_threshold=2.0,
            verbose=True
        )

        # Add verification result to match
        match['verified_by_artifacts'] = verification_result['verified']
        match['verification_confidence'] = verification_result['confidence']
        match['matched_features'] = verification_result['matched_features']

        if verification_result['verified']:
            verified_matches.append(match)
            print(f"[+] VERIFIED: Artifacts match letter structure")
        else:
            print(f"[!] NOT VERIFIED: Artifacts do not match")

    results['verified_matches'] = verified_matches

    if not verified_matches:
        print("\n[!] No matches verified by artifact analysis.")
        return results

    # ========================================================================
    # PHASE D: EVIDENCE GENERATION
    # ========================================================================
    print(f"\n[*] Generating evidence cards for {len(verified_matches)} verified matches...")

    os.makedirs(evidence_output_dir, exist_ok=True)

    evidence_generator = EvidenceCardGenerator(dpi=dpi, font_path=font_path)

    for i, match in enumerate(verified_matches):
        redaction_idx = match['redaction_idx']
        candidate_name = match['name']

        # Generate safe filename
        safe_name = candidate_name.replace(" ", "_").replace("-", "_").lower()
        evidence_path = f"{evidence_output_dir}/match_{i:03d}_{safe_name}.png"

        # Find highlight position if there are ascenders
        highlight_pos = None
        for j, char in enumerate(candidate_name):
            if char in 'bdfhijkltABDFHIJKLT':
                highlight_pos = j
                break

        try:
            output_path = evidence_generator.create_evidence_card(
                pdf_path=pdf_path,
                redaction_index=redaction_idx,
                candidate_name=candidate_name,
                highlight_pos=highlight_pos,
                output_dir=evidence_output_dir
            )
            match['evidence_card'] = output_path
            print(f"[+] Evidence: {output_path}")
        except Exception as e:
            print(f"[!] Failed to generate evidence card: {e}")
            match['evidence_card'] = None

    return results


def print_final_report(results: Dict, report_path: str):
    """Print the final report and save to file."""
    verified_matches = results['verified_matches']

    print("\n" + "=" * 60)
    print("SOLVED REDACTIONS:")
    print("=" * 60)

    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("FORENSIC REDACTION SOLUTION REPORT")
    report_lines.append("=" * 60)
    report_lines.append(f"Document: {results['pdf_path']}")
    report_lines.append(f"Total Matches: {len(results['matches'])}")
    report_lines.append(f"Verified Matches: {len(verified_matches)}")
    report_lines.append("")

    for i, match in enumerate(verified_matches, 1):
        redaction_idx = match['redaction_idx']
        candidate_name = match['name']
        score = match['score']
        context_boost = match.get('context_boost', 0)
        features = match.get('matched_features', [])
        evidence_path = match.get('evidence_card', 'N/A')

        # Determine context string
        context_str = "Width Match"
        if context_boost > 0:
            context_str = f"Context: 'with' + {context_str}"

        # Determine status message
        if features:
            feature_summary = ', '.join(features[:2])  # Show up to 2 features
            status_msg = f"CONFIRMED ({feature_summary})"
        else:
            status_msg = "CONFIRMED (Artifacts match letter structure)"

        # Print console output
        print(f"\n{i}. Page 1, Redaction #{redaction_idx + 1}")
        print(f"   MATCH: \"{candidate_name}\"")
        print(f"   CONFIDENCE: {score:.0f}% ({context_str})")
        print(f"   STATUS: {status_msg}")
        print(f"   EVIDENCE: {evidence_path}")
        print("   " + "-" * 56)

        # Add to report
        report_lines.append(f"Match #{i}:")
        report_lines.append(f"  Redaction: #{redaction_idx + 1}")
        report_lines.append(f"  Name: {candidate_name}")
        report_lines.append(f"  Confidence: {score:.1f}%")
        report_lines.append(f"  Context: {context_str}")
        report_lines.append(f"  Status: {status_msg}")
        report_lines.append(f"  Evidence: {evidence_path}")
        report_lines.append("")

    # Save report to file
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))

    print(f"\n[!] Full technical report saved to: {report_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Solve Redactions - One-Click Master Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python solve_redactions.py --pdf files/document.pdf --candidates candidates.csv
    python solve_redactions.py --pdf files/document.pdf --candidates candidates.csv --confidence 95
    python solve_redactions.py --pdf files/document.pdf --candidates candidates.csv --output my_results/
        """
    )

    parser.add_argument('--pdf', type=str, required=True,
                        help='Path to PDF file to analyze')
    parser.add_argument('--candidates', type=str, default='candidates.csv',
                        help='Path to CSV file with candidate names (default: candidates.csv)')
    parser.add_argument('--confidence', type=float, default=90.0,
                        help='Minimum confidence threshold for verification (default: 90.0)')
    parser.add_argument('--dpi', type=int, default=600,
                        help='DPI for PDF conversion (default: 600)')
    parser.add_argument('--output', type=str, default='solved_evidence',
                        help='Output directory for evidence cards (default: solved_evidence)')
    parser.add_argument('--report', type=str, default='solution_report.txt',
                        help='Path to solution report (default: solution_report.txt)')

    args = parser.parse_args()

    # Validate inputs
    if not os.path.exists(args.pdf):
        print(f"[ERROR] PDF file not found: {args.pdf}")
        return 1

    if not os.path.exists(args.candidates):
        print(f"[ERROR] Candidates CSV not found: {args.candidates}")
        return 1

    # Load candidates
    try:
        candidates = load_candidates(args.candidates)
        print(f"[*] Loaded {len(candidates)} candidates from {args.candidates}")
    except Exception as e:
        print(f"[ERROR] Failed to load candidates: {e}")
        return 1

    # Run analysis
    try:
        results = run_master_analysis(
            pdf_path=args.pdf,
            candidates=candidates,
            dpi=args.dpi,
            confidence_threshold=args.confidence,
            evidence_output_dir=args.output,
            report_path=args.report
        )

        # Print final report
        if results['verified_matches']:
            print_final_report(results, args.report)
        else:
            print("\n[!] No verified matches found. No report generated.")

        return 0

    except KeyboardInterrupt:
        print("\n[!] Analysis interrupted by user")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
