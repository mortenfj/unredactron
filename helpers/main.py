#!/usr/bin/env python3
"""
Unredactron - Digital forensic tool for analyzing redacted PDF documents.
Locally adapted from the Google Colab notebook.
"""

import cv2
import numpy as np
import pytesseract
import pandas as pd
from pdf2image import convert_from_path
from PIL import Image, ImageFont, ImageDraw
import os


class RedactionCracker:
    def __init__(self, font_path, font_size_pt=12):
        self.font_path = font_path
        self.font_size_pt = font_size_pt
        try:
            self.font = ImageFont.truetype(font_path, font_size_pt)
        except:
            raise ValueError(f"Could not load font: {font_path}")

        self.px_per_pt = 0 # Will be calibrated
        self.tracking_px = 0 # Will be calibrated

    def calibrate(self, image_cv, control_word):
        """
        Finds a known word in the image to determine exact DPI and Tracking.
        """
        print(f"Calibrating using control word: '{control_word}'...")

        # 1. OCR to find the word's bounding box
        h, w, _ = image_cv.shape
        data = pytesseract.image_to_data(image_cv, output_type=pytesseract.Output.DICT)

        target_box = None
        for i, text in enumerate(data['text']):
            if control_word.lower() in text.lower():
                # Found it
                (x, y, w_box, h_box) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
                target_box = (x, y, w_box, h_box)
                print(f"   -> Found '{text}' at width {w_box}px")
                break

        if not target_box:
            print("ERROR: Calibration Failed - Control word not found via OCR.")
            return False

        # 2. Reverse Engineer the DPI/Scale
        # We assume the font size is 12pt (standard).
        # Theoretical width without tracking:
        base_len = self.font.getlength(control_word)

        # If the real box is wider, the difference is Tracking (or Scale error)
        # We assume standard scale first to find tracking.
        real_width = target_box[2]

        # Simple Calibration: Calculate a global scaling factor
        # (This combines DPI and Tracking into one 'Effective Pixel Width' ratio)
        self.scale_factor = real_width / base_len
        print(f"   -> Calibration Locked. Scale Factor: {self.scale_factor:.4f}")
        return True

    def find_redactions(self, image_cv):
        """
        Locates black bars using Computer Vision contours.
        """
        # Grayscale & Threshold
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY_INV) # Invert: Black becomes White

        # Find Contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        redactions = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            # Filter noise: Must be wider than high, and decent size
            if w > 30 and h > 10 and w/h > 1.5:
                redactions.append((x, y, w, h))

        # Sort by Y position (reading order)
        redactions.sort(key=lambda b: b[1])
        return redactions

    def check_width_match(self, name, target_width_px, tolerance=2.0):
        """
        Checks if a name fits the width using the Calibrated Scale.
        """
        # Calculate theoretical width in standard font
        base_width = self.font.getlength(name)

        # Apply our calibrated scale factor
        predicted_width = base_width * self.scale_factor

        if abs(predicted_width - target_width_px) <= tolerance:
            return True, predicted_width
        return False, predicted_width

    def artifact_check(self, name, image_cv, box_coords):
        """
        Checks for stray pixels (artifacts) on the left/right of the box.
        This is a simplified check for the 'First Letter' artifact.
        """
        x, y, w, h = box_coords

        # Extract the region slightly larger than the black box
        margin = 5
        roi = image_cv[y-margin:y+h+margin, x-margin:x+w+margin]

        # If the name starts with 'S', do we see pixels at the top-left?
        # (This requires complex template matching, we will output a score based on 'fill')
        # Placeholder for the advanced alignment logic discussed previously.
        return "Not Implemented in Basic Mode"


# --- CONFIGURATION ---
# Update these paths for your local environment
FILE_PATH = "files/EFTA00037366.pdf"  # PDF or Image
FONT_PATH = "fonts/fonts/times.ttf"   # Must match document font
CONTROL_WORD = "Subject:"              # A word visible on the page to calibrate scale
SUSPECT_LIST = [
    "Sarah Kellen", "Ghislaine Maxwell", "Nadia Marcinkova",
    "Lesley Groff", "Bill Hammond", "Jeffrey Epstein",
    "Bill Clinton", "Prince Andrew", "Emmy Taylor"
]


def run_investigation():
    """Main investigation pipeline."""
    print("=" * 50)
    print("UNREDACTRON - Forensic PDF Analysis")
    print("=" * 50)

    # 0. Validate inputs
    print(f"\n[*] Configuration:")
    print(f"    Target: {FILE_PATH}")
    print(f"    Font: {FONT_PATH}")
    print(f"    Control Word: '{CONTROL_WORD}'")
    print(f"    Suspects: {len(SUSPECT_LIST)} names")

    # 1. Load Document
    print(f"\n[*] Loading document...")
    if FILE_PATH.lower().endswith('.pdf'):
        pages = convert_from_path(FILE_PATH)
        print(f"    -> PDF loaded: {len(pages)} pages")
    else:
        img = cv2.imread(FILE_PATH)
        pages = [img]
        print(f"    -> Image loaded")

    # 2. Initialize Engine (calibrate on first page)
    print(f"\n[*] Initializing forensic engine...")
    img = np.array(pages[0])
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    try:
        engine = RedactionCracker(FONT_PATH, font_size_pt=12)  # Times New Roman 12pt
        print(f"    -> Font loaded successfully: Times New Roman 12pt")
    except ValueError as e:
        print(f"ERROR: {e}")
        return

    # 3. Calibrate
    print(f"\n[*] Calibrating document scale...")
    if not engine.calibrate(img, CONTROL_WORD):
        print("    -> Calibration failed - cannot proceed")
        return

    # 4. Analyze all pages
    print(f"\n[*] Scanning all pages for redactions...")
    all_matches = []

    for page_num, page in enumerate(pages, 1):
        img = np.array(page)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        redactions = engine.find_redactions(img)

        if len(redactions) == 0:
            continue

        print(f"\n--- Page {page_num}: {len(redactions)} redaction(s) ---")

        # Test each redaction
        for box in redactions:
            x, y, w, h = box

            matches = []
            for name in SUSPECT_LIST:
                variations = [name, name.upper()]

                for variant in variations:
                    match, pred_w = engine.check_width_match(variant, w, tolerance=15.0)
                    if match:
                        matches.append((variant, pred_w))

            if matches:
                for variant, pred_w in matches:
                    diff = abs(pred_w - w)
                    print(f"  [P{page_num}] {w}px redaction: '{variant}' (pred: {pred_w:.1f}px, diff: {diff:+.1f}px)")
                    all_matches.append((page_num, x, y, w, h, variant, pred_w))

    # Summary
    print("\n" + "=" * 50)
    if all_matches:
        print(f"ANALYSIS COMPLETE: Found {len(all_matches)} potential matches")
        print("=" * 50)

        # Count by name
        name_counts = {}
        for match in all_matches:
            name = match[5]
            name_counts[name] = name_counts.get(name, 0) + 1

        print("\nMatch frequency:")
        for name, count in sorted(name_counts.items(), key=lambda x: -x[1]):
            print(f"  {name}: {count} occurrence(s)")
    else:
        print("ANALYSIS COMPLETE: No matches found")
    print("=" * 50)


if __name__ == "__main__":
    run_investigation()
