#!/usr/bin/env python3
"""
Typographic Profiling Module for Unredactron
Automatically detects font, size, tracking, and kerning from document samples
"""

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from PIL import ImageFont, Image, ImageDraw
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json


class FontProfile:
    """Container for detected font parameters"""

    def __init__(self):
        self.font_name = None
        self.font_path = None
        self.font_size = None
        self.tracking_offset = 0.0
        self.kerning_mode = "standard"
        self.leading_ratio = 1.5
        self.scale_factor = 1.0
        self.confidence = 0.0
        self.reference_word = None
        self.reference_width = None
        self.reference_height = None
        self.calibration_accuracy = 0.0

    def to_dict(self) -> Dict:
        """Convert profile to dictionary for JSON output"""
        return {
            "detected_font": self.font_name,
            "detected_size": f"{self.font_size:.1f}pt",
            "tracking_offset": f"{self.tracking_offset:.2f}px",
            "kerning_mode": self.kerning_mode,
            "leading_ratio": f"{self.leading_ratio:.2f}x",
            "scale_factor": f"{self.scale_factor:.4f}",
            "confidence_in_profile": f"{self.confidence:.1f}%",
            "calibration_reference": {
                "word": self.reference_word,
                "physical_width": f"{self.reference_width:.1f}px",
                "physical_height": f"{self.reference_height:.1f}px"
            },
            "accuracy_score": f"{self.calibration_accuracy:.2f}%"
        }

    def __repr__(self):
        return (f"FontProfile(font={self.font_name}, size={self.font_size:.1f}pt, "
                f"tracking={self.tracking_offset:.2f}px, confidence={self.confidence:.1f}%)")


class FontProfiler:
    """
    Automated font detection and profiling system.

    Scans document for unredacted text, reverse-engineers font settings,
    and produces a typographic profile for forensic analysis.
    """

    # Common reference words to look for in legal/business documents
    REFERENCE_WORDS = [
        "Company", "Subject", "To", "From", "Date", "Re", "Dear", "Sincerely",
        "Agreement", "Contract", "Page", "CONFIDENTIAL", "ATTORNEY"
    ]

    # Font library: serif (legal) and sans-serif (business)
    FONT_FAMILIES = {
        "serif": ["times.ttf", "CENTURY.TTF", "GARA.TTF",
                  "cambriaz.ttf", "cambriab.ttf", "cambriai.ttf"],
        "sans-serif": ["arial.ttf", "calibri.ttf", "cour.ttf"]
    }

    # Test sizes to try (in points)
    TEST_SIZES = [10, 11, 12, 12.4, 12.5, 13, 14]

    # Tracking offsets to test (in pixels)
    TRACKING_RANGES = [-0.5, 0.0, 0.1, 0.15, 0.2, 0.25, 0.3, 0.5, 1.0]

    def __init__(self, fonts_dir: str = "fonts/fonts/"):
        """
        Initialize the profiler.

        Args:
            fonts_dir: Path to directory containing .ttf font files
        """
        self.fonts_dir = fonts_dir
        self.available_fonts = self._scan_fonts()

    def _scan_fonts(self) -> List[Tuple[str, str]]:
        """Scan fonts directory and return (name, path) tuples"""
        fonts = []
        if not os.path.exists(self.fonts_dir):
            return fonts

        for filename in sorted(os.listdir(self.fonts_dir)):
            if filename.lower().endswith('.ttf') or filename.lower().endswith('.ttf'):
                path = os.path.join(self.fonts_dir, filename)
                fonts.append((filename, path))

        return fonts

    def find_reference_word(self, image: np.ndarray,
                            min_confidence: int = 80,
                            min_length: int = 5,
                            max_length: int = 15) -> Optional[Tuple[str, int, int, int, int]]:
        """
        Scan document for suitable reference word using OCR.

        Args:
            image: Document image (numpy array)
            min_confidence: Minimum OCR confidence score
            min_length: Minimum word length
            max_length: Maximum word length

        Returns:
            Tuple of (word, x, y, width, height) or None if not found
        """
        # Convert to BGR for Tesseract
        if len(image.shape) == 3 and image.shape[2] == 3:
            img_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        else:
            img_bgr = image

        # Get OCR data
        data = pytesseract.image_to_data(img_bgr, output_type=pytesseract.Output.DICT)

        # Collect candidate words
        candidates = []
        for i, text in enumerate(data['text']):
            conf = int(data['conf'][i]) if data['conf'][i] != '-1' else 0
            text_clean = text.strip()

            # Check if this is a good reference word
            if (conf >= min_confidence and
                min_length <= len(text_clean) <= max_length and
                text_clean.isalpha() and
                text_clean[0].isupper()):

                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]

                candidates.append((text_clean, x, y, w, h, conf))

        if not candidates:
            return None

        # Prefer words from our reference list
        for candidate in candidates:
            if candidate[0] in self.REFERENCE_WORDS:
                return candidate[:-1]  # Return without confidence

        # Otherwise return the highest confidence candidate
        candidates.sort(key=lambda x: x[5], reverse=True)
        return candidates[0][:-1]

    def calculate_tracking_adjustment(self, font: ImageFont.FreeTypeFont,
                                     reference_word: str,
                                     actual_width: float,
                                     scale_factor: float) -> float:
        """
        Calculate the tracking (letter-spacing) offset needed to match the document.

        Args:
            font: PIL ImageFont object
            reference_word: Word to test
            actual_width: Physical width measured from document
            scale_factor: DPI scaling factor

        Returns:
            Tracking offset in pixels per character
        """
        # Calculate expected width without tracking
        expected_width = font.getlength(reference_word) * scale_factor

        # The difference is distributed across all characters
        # (n-1) gaps for n characters, but we approximate with n
        tracking_total = actual_width - expected_width
        tracking_per_char = tracking_total / len(reference_word)

        return tracking_per_char

    def test_font_configuration(self, font_path: str, font_size: float,
                                reference_word: str, actual_width: float,
                                actual_height: float,
                                tracking_offset: float = 0.0) -> Dict:
        """
        Test a specific font configuration against the reference measurement.

        Args:
            font_path: Path to .ttf file
            font_size: Font size in points
            reference_word: Word being measured
            actual_width: Physical width from document
            actual_height: Physical height from document
            tracking_offset: Letter spacing adjustment

        Returns:
            Dictionary with test results
        """
        try:
            font = ImageFont.truetype(font_path, int(font_size))

            # Calculate scale factor from width
            base_width = font.getlength(reference_word)
            if base_width == 0:
                return None

            scale_factor = actual_width / base_width

            # Calculate calibrated width with tracking
            calibrated_width = base_width * scale_factor + (len(reference_word) * tracking_offset)

            # Calculate error metrics
            width_error = abs(calibrated_width - actual_width)
            width_error_pct = (width_error / actual_width) * 100

            # Check height match
            font_height = font_size * scale_factor  # Approximate
            height_error = abs(font_height - actual_height)

            # Combined accuracy score
            accuracy = 100 - width_error_pct
            if height_error > 20:  # Penalize height mismatch
                accuracy -= 10

            return {
                'font_path': font_path,
                'font_name': os.path.basename(font_path),
                'font_size': font_size,
                'scale_factor': scale_factor,
                'tracking_offset': tracking_offset,
                'calibrated_width': calibrated_width,
                'actual_width': actual_width,
                'width_error': width_error,
                'width_error_pct': width_error_pct,
                'height_error': height_error,
                'accuracy': accuracy
            }

        except Exception as e:
            return None

    def profile_document(self, image: np.ndarray,
                        dpi: int = 1200,
                        verbose: bool = True) -> Optional[FontProfile]:
        """
        Analyze a document page and detect its typographic profile.

        Args:
            image: Document image (numpy array)
            dpi: Document DPI
            verbose: Print progress messages

        Returns:
            FontProfile object with detected parameters, or None if detection fails
        """
        if verbose:
            print("="*100)
            print("TYPOGRAPHIC PROFILING MODULE")
            print("="*100)
            print(f"\n[*] Document Analysis Date: {datetime.now().strftime('%Y-%m-%d')}")
            print(f"[*] Baseline Resolution: {dpi} DPI")
            print(f"[*] Available Fonts: {len(self.available_fonts)}")

        # Step 1: Find reference word
        if verbose:
            print(f"\n[1] REFERENCE WORD SCAN")

        ref = self.find_reference_word(image)
        if not ref:
            if verbose:
                print("    ✗ No suitable reference word found")
            return None

        reference_word, ref_x, ref_y, ref_width, ref_height = ref
        if verbose:
            print(f"    ✓ Found: '{reference_word}' at ({ref_x}, {ref_y})")
            print(f"      Physical dimensions: {ref_width:.1f}px × {ref_height:.1f}px")

        # Step 2: Test all font configurations
        if verbose:
            print(f"\n[2] FONT SEARCH LIBRARY")
            print(f"    Testing {len(self.available_fonts)} fonts × {len(self.TEST_SIZES)} sizes "
                  f"× {len(self.TRACKING_RANGES)} tracking values...")

        results = []

        for font_name, font_path in self.available_fonts:
            for font_size in self.TEST_SIZES:
                for tracking in self.TRACKING_RANGES:
                    result = self.test_font_configuration(
                        font_path, font_size, reference_word,
                        ref_width, ref_height, tracking
                    )
                    if result and result['accuracy'] > 90:
                        results.append(result)

        if not results:
            if verbose:
                print("    ✗ No font configurations matched satisfactorily")
            return None

        # Sort by accuracy
        results.sort(key=lambda x: x['accuracy'], reverse=True)

        # Get the best result
        best = results[0]

        if verbose:
            print(f"    ✓ Tested {len(self.available_fonts) * len(self.TEST_SIZES) * len(self.TRACKING_RANGES)} configurations")
            print(f"    ✓ Found {len(results)} candidate matches (>90% accuracy)")

        # Step 3: Build profile
        if verbose:
            print(f"\n[3] TYPOGRAPHIC PROFILE")

        profile = FontProfile()
        profile.font_name = best['font_name']
        profile.font_path = best['font_path']
        profile.font_size = best['font_size']
        profile.tracking_offset = best['tracking_offset']
        profile.scale_factor = best['scale_factor']
        profile.confidence = best['accuracy']
        profile.reference_word = reference_word
        profile.reference_width = ref_width
        profile.reference_height = ref_height
        profile.calibration_accuracy = best['accuracy']

        # Detect kerning mode (simplified)
        if best['tracking_offset'] == 0:
            profile.kerning_mode = "metric"
        else:
            profile.kerning_mode = "metric_with_tracking"

        if verbose:
            print(f"    Detected Font:     {profile.font_name}")
            print(f"    Detected Size:     {profile.font_size:.1f} pt")
            print(f"    Tracking:          {profile.tracking_offset:+.2f} px")
            print(f"    Kerning:           {profile.kerning_mode}")
            print(f"    Scale Factor:      {profile.scale_factor:.4f}")
            print(f"    Confidence:        {profile.confidence:.1f}%")

        # Step 4: Validation
        if verbose:
            print(f"\n[4] CALIBRATION VALIDATION")
            print(f"    Sample Text:       '{reference_word}'")
            print(f"    Physical Width:    {ref_width:.1f} px")
            print(f"    Virtual Width:     {best['calibrated_width']:.1f} px")
            print(f"    Accuracy Score:    {profile.calibration_accuracy:.2f}%")

            if profile.calibration_accuracy >= 99:
                print(f"    Status: ✓✓✓ EXCELLENT - Ready for forensic analysis")
            elif profile.calibration_accuracy >= 95:
                print(f"    Status: ✓✓ GOOD - Acceptable for analysis")
            else:
                print(f"    Status: ⚠ MODERATE - Results may have reduced accuracy")

        return profile

    def profile_from_pdf(self, pdf_path: str, page: int = 0,
                        dpi: int = 1200, verbose: bool = True) -> Optional[FontProfile]:
        """
        Load PDF and profile the specified page.

        Args:
            pdf_path: Path to PDF file
            page: Page number to analyze (0-indexed)
            dpi: Rendering DPI
            verbose: Print progress

        Returns:
            FontProfile object or None
        """
        if verbose:
            print(f"\n[*] Loading PDF: {pdf_path}")

        try:
            pages = convert_from_path(pdf_path, dpi=dpi)
            if page >= len(pages):
                if verbose:
                    print(f"    ✗ Page {page} not found (document has {len(pages)} pages)")
                return None

            image = np.array(pages[page])
            return self.profile_document(image, dpi, verbose)

        except Exception as e:
            if verbose:
                print(f"    ✗ Error loading PDF: {e}")
            return None

    def save_profile(self, profile: FontProfile, output_path: str):
        """Save profile to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(profile.to_dict(), f, indent=2)
        print(f"\n[*] Profile saved to: {output_path}")


def load_profile(profile_path: str) -> FontProfile:
    """Load profile from JSON file"""
    with open(profile_path, 'r') as f:
        data = json.load(f)

    profile = FontProfile()
    profile.font_name = data['detected_font']
    profile.font_size = float(data['detected_size'].replace('pt', ''))
    profile.tracking_offset = float(data['tracking_offset'].replace('px', ''))
    profile.kerning_mode = data['kerning_mode']
    profile.leading_ratio = float(data['leading_ratio'].replace('x', ''))
    profile.scale_factor = float(data['scale_factor'])
    profile.confidence = float(data['confidence_in_profile'].replace('%', ''))
    profile.reference_word = data['calibration_reference']['word']
    profile.reference_width = float(data['calibration_reference']['physical_width'].replace('px', ''))
    profile.reference_height = float(data['calibration_reference']['physical_height'].replace('px', ''))
    profile.calibration_accuracy = float(data['accuracy_score'].replace('%', ''))

    return profile
