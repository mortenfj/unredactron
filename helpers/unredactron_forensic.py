#!/usr/bin/env python3
"""
Integrated Forensic Analysis - Combines Width Matching + Artifact Detection

This script combines the original Unredactron width-based analysis with the new
Forensic Halo Extraction module for comprehensive redaction analysis.

Features:
- Original width-based candidate matching
- Enhanced halo extraction with corner exclusion
- Side-wall separation (top/bottom/left/right)
- Forensic enhancement pipeline
- Composite forensic sheets for high-confidence matches

Usage:
    python unredactron_forensic.py --file files/document.pdf --font fonts/fonts/times.ttf
    python unredactron_forensic.py --file files/document.pdf --diagnostic-mode
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image, ImageFont, ImageDraw
import pandas as pd
import argparse
import os
import sys

# Add helpers to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from helpers.forensic_halo import ForensicHaloExtractor


class ForensicRedactionAnalyzer:
    """
    Comprehensive redaction analysis combining width matching and artifact detection.
    """

    def __init__(
        self,
        file_path: str,
        font_path: str,
        dpi: int = 600,
        diagnostic_mode: bool = False,
        control_word: str = None,
        tolerance: float = 3.0
    ):
        """
        Initialize the forensic analyzer.

        Args:
            file_path: Path to PDF document
            font_path: Path to matching TrueType font
            dpi: DPI for PDF conversion
            diagnostic_mode: Enable forensic sheet generation
            control_word: Visible word for calibration (optional)
            tolerance: Width matching tolerance in pixels
        """
        self.file_path = file_path
        self.font_path = font_path
        self.dpi = dpi
        self.diagnostic_mode = diagnostic_mode
        self.control_word = control_word
        self.tolerance = tolerance

        # Initialize halo extractor
        self.halo_extractor = ForensicHaloExtractor(
            dpi=dpi,
            halo_thickness=6,
            corner_radius=15
        )

        # Load document
        self._load_document()

        # Load font
        self.font = self._load_font()

    def _load_document(self):
        """Convert PDF to high-DPI image."""
        print(f"[INFO] Converting PDF to {self.dpi} DPI...")
        images = convert_from_path(self.file_path, dpi=self.dpi)
        self.image = np.array(images[0])
        self.gray = cv2.cvtColor(self.image, cv2.COLOR_RGB2GRAY)
        print(f"[INFO] Image size: {self.image.shape[1]}x{self.image.shape[0]}px")

    def _load_font(self) -> ImageFont.FreeTypeFont:
        """Load the TrueType font with proper scaling."""
        base_size = 12
        # Scale font size based on DPI
        scaled_size = int(base_size * self.dpi / 72)
        try:
            return ImageFont.truetype(self.font_path, scaled_size)
        except Exception as e:
            print(f"[ERROR] Failed to load font: {e}")
            raise

    def calibrate_with_control_word(self, control_word: str) -> float:
        """
        Calibrate using a visible control word.

        Returns the scale factor for width predictions.
        """
        print(f"\n[INFO] Calibrating with control word: '{control_word}'")

        # Use OCR to find the control word
        import pytesseract
        from pytesseract import Output

        # Get OCR data with bounding boxes
        d = pytesseract.image_to_data(
            self.gray,
            output_type=Output.DICT
        )

        # Find the control word
        scale_factor = 1.0
        found = False

        for i, text in enumerate(d['text']):
            if control_word.lower() in text.lower():
                x, y, w, h = d['left'][i], d['top'][i], d['width'][i], d['height'][i]

                # Calculate expected width
                temp_img = Image.new('RGB', (1000, 100), 'white')
                temp_draw = ImageDraw.Draw(temp_img)
                bbox = temp_draw.textbbox((0, 0), control_word, font=self.font)
                expected_width = bbox[2] - bbox[0]

                # Calculate scale factor
                scale_factor = w / expected_width
                found = True
                print(f"[INFO] Control word found at ({x}, {y}), actual width: {w}px")
                print(f"[INFO] Expected width: {expected_width}px, scale factor: {scale_factor:.2f}")
                break

        if not found:
            print(f"[WARNING] Control word not found, using scale factor of 1.0")

        return scale_factor

    def find_redactions(self, min_width: int = 200, min_height: int = 100) -> list:
        """
        Find redaction boxes in the document.

        Args:
            min_width: Minimum width for name-sized redactions
            min_height: Minimum height

        Returns:
            List of (x, y, w, h) bounding boxes
        """
        print(f"\n[INFO] Locating redaction boxes...")

        # Threshold to find black areas
        _, black_mask = cv2.threshold(self.gray, 15, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(
            black_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Extract and filter redactions
        redactions = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > min_width and h > min_height:
                redactions.append((x, y, w, h))

        redactions.sort(key=lambda b: b[1])
        print(f"[INFO] Found {len(redactions)} redaction boxes")

        return redactions

    def calculate_text_width(self, text: str, scale_factor: float = 1.0) -> int:
        """
        Calculate the expected pixel width of text.

        Args:
            text: Text string to measure
            scale_factor: Calibration scale factor

        Returns:
            Expected width in pixels
        """
        temp_img = Image.new('RGB', (1000, 100), 'white')
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), text, font=self.font)
        width = bbox[2] - bbox[0]

        return int(width * scale_factor)

    def match_candidates_to_redactions(
        self,
        candidates: list,
        redactions: list,
        scale_factor: float = 1.0
    ) -> list:
        """
        Match candidate names to redactions based on width.

        Args:
            candidates: List of candidate names or dict with 'name' key
            redactions: List of (x, y, w, h) redaction boxes
            scale_factor: Calibration scale factor

        Returns:
            List of match dictionaries with width and artifact analysis
        """
        print(f"\n[INFO] Matching {len(candidates)} candidates to {len(redactions)} redactions...")

        matches = []

        for redaction_idx, (rx, ry, rw, rh) in enumerate(redactions):
            print(f"\n{'-'*80}")
            print(f"Redaction #{redaction_idx + 1} at ({rx}, {ry}), size: {rw}x{rh}px")

            best_match = None
            best_score = 0

            for candidate in candidates:
                # Handle both string and dict formats
                if isinstance(candidate, dict):
                    name = candidate['name']
                    confidence = candidate.get('confidence', 1.0)
                else:
                    name = candidate
                    confidence = 1.0

                # Calculate expected width
                expected_width = self.calculate_text_width(name, scale_factor)
                width_error = abs(rw - expected_width)

                # Check if within tolerance
                if width_error <= self.tolerance:
                    # Calculate match score
                    width_score = 100 - (width_error / expected_width * 100)
                    combined_score = width_score * confidence

                    if combined_score > best_score:
                        best_score = combined_score
                        best_match = {
                            'name': name,
                            'confidence': confidence,
                            'expected_width': expected_width,
                            'actual_width': rw,
                            'width_error': width_error,
                            'score': combined_score
                        }

            # Perform artifact analysis for best match
            if best_match:
                print(f"  BEST MATCH: {best_match['name']}")
                print(f"    Expected width: {best_match['expected_width']}px")
                print(f"    Actual width: {best_match['actual_width']}px")
                print(f"    Width error: {best_match['width_error']:.2f}px")
                print(f"    Match score: {best_match['score']:.1f}%")

                # Extract and analyze halo
                halo_data = self.halo_extractor.extract_halo_with_corner_exclusion(
                    self.gray, (rx, ry, rw, rh)
                )

                enhanced = self.halo_extractor.apply_forensic_enhancement(halo_data['full'])
                artifact_metrics = self.halo_extractor.analyze_halo_for_artifacts(halo_data)

                # Calculate artifact confidence
                artifact_confidence = (
                    artifact_metrics.get('top_artifact_score', 0) * 0.3 +
                    artifact_metrics.get('bottom_artifact_score', 0) * 0.3 +
                    artifact_metrics.get('left_artifact_score', 0) * 0.2 +
                    artifact_metrics.get('right_artifact_score', 0) * 0.2
                )

                best_match['artifact_metrics'] = artifact_metrics
                best_match['artifact_confidence'] = artifact_confidence
                best_match['has_artifacts'] = artifact_confidence > 1.0

                print(f"\n  ARTIFACT ANALYSIS:")
                print(f"    Top wall:    {artifact_metrics.get('top_dark_pixels', 0)} dark pixels")
                print(f"    Bottom wall: {artifact_metrics.get('bottom_dark_pixels', 0)} dark pixels")
                print(f"    Left wall:   {artifact_metrics.get('left_dark_pixels', 0)} dark pixels")
                print(f"    Right wall:  {artifact_metrics.get('right_dark_pixels', 0)} dark pixels")
                print(f"    Artifact confidence: {artifact_confidence:.2f}%")

                # Generate forensic sheet if diagnostic mode enabled
                if self.diagnostic_mode and artifact_confidence > 1.0:
                    output_dir = "forensic_output"
                    os.makedirs(output_dir, exist_ok=True)

                    output_path = f"{output_dir}/match_{redaction_idx:03d}_{best_match['name'].replace(' ', '_')}.png"
                    self.halo_extractor.create_forensic_sheet(
                        self.gray,
                        halo_data,
                        enhanced,
                        (rx, ry, rw, rh),
                        candidate_name=best_match['name'],
                        output_path=output_path
                    )
                    print(f"    ✓ Forensic sheet saved: {output_path}")

                best_match['redaction_idx'] = redaction_idx
                best_match['redaction_coords'] = (rx, ry, rw, rh)

                matches.append(best_match)
            else:
                print(f"  No match within tolerance ({self.tolerance}px)")

        return matches

    def generate_report(self, matches: list, output_path: str = "forensic_report.txt"):
        """Generate a text report of the analysis."""
        with open(output_path, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("FORENSIC REDACTION ANALYSIS REPORT\n")
            f.write("=" * 100 + "\n\n")

            f.write(f"Document: {self.file_path}\n")
            f.write(f"Font: {self.font_path}\n")
            f.write(f"DPI: {self.dpi}\n")
            f.write(f"Tolerance: {self.tolerance}px\n\n")

            f.write(f"Total matches found: {len(matches)}\n\n")

            for match in matches:
                f.write("-" * 80 + "\n")
                f.write(f"Redaction #{match['redaction_idx'] + 1}\n")
                f.write(f"  Location: {match['redaction_coords']}\n")
                f.write(f"  Match: {match['name']}\n")
                f.write(f"  Width Match: {match['score']:.1f}%\n")
                f.write(f"  Artifact Confidence: {match['artifact_confidence']:.2f}%\n")
                f.write(f"  Has Artifacts: {'YES' if match['has_artifacts'] else 'NO'}\n")

                if match['has_artifacts']:
                    f.write(f"  Artifact Details:\n")
                    am = match['artifact_metrics']
                    f.write(f"    Top: {am.get('top_dark_pixels', 0)} dark pixels\n")
                    f.write(f"    Bottom: {am.get('bottom_dark_pixels', 0)} dark pixels\n")
                    f.write(f"    Left: {am.get('left_dark_pixels', 0)} dark pixels\n")
                    f.write(f"    Right: {am.get('right_dark_pixels', 0)} dark pixels\n")

        print(f"\n[INFO] Report saved to: {output_path}")


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Forensic Redaction Analysis - Width Matching + Artifact Detection"
    )
    parser.add_argument('--file', required=True, help='Path to PDF document')
    parser.add_argument('--font', required=True, help='Path to TrueType font file')
    parser.add_argument('--csv', help='Path to CSV with candidates (columns: name, confidence)')
    parser.add_argument('--candidates', nargs='+', help='Candidate names (space-separated)')
    parser.add_argument('--dpi', type=int, default=600, help='DPI for PDF conversion (default: 600)')
    parser.add_argument('--tolerance', type=float, default=3.0, help='Width tolerance in pixels (default: 3.0)')
    parser.add_argument('--control-word', help='Visible word for calibration')
    parser.add_argument('--diagnostic-mode', action='store_true', help='Generate forensic sheets')
    parser.add_argument('--output', default='forensic_report.txt', help='Report output path')

    args = parser.parse_args()

    # Load candidates
    if args.csv:
        df = pd.read_csv(args.csv)
        candidates = df.to_dict('records')
    elif args.candidates:
        candidates = args.candidates
    else:
        print("[ERROR] Must provide --csv or --candidates")
        parser.print_help()
        sys.exit(1)

    # Initialize analyzer
    analyzer = ForensicRedactionAnalyzer(
        file_path=args.file,
        font_path=args.font,
        dpi=args.dpi,
        diagnostic_mode=args.diagnostic_mode,
        control_word=args.control_word,
        tolerance=args.tolerance
    )

    # Calibrate if control word provided
    scale_factor = 1.0
    if args.control_word:
        scale_factor = analyzer.calibrate_with_control_word(args.control_word)

    # Find redactions
    redactions = analyzer.find_redactions()

    # Match candidates
    matches = analyzer.match_candidates_to_redactions(
        candidates=candidates,
        redactions=redactions,
        scale_factor=scale_factor
    )

    # Generate report
    analyzer.generate_report(matches, args.output)

    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    main()
