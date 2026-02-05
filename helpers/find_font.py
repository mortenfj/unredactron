#!/usr/bin/env python3
"""
Test all available fonts to find which one matches the document best.
"""

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from PIL import ImageFont
import os

FILE_PATH = "files/EFTA00513855.pdf"
CONTROL_WORD = "Contacts"
FONTS_DIR = "fonts/fonts/"

# Test names - use a variety of widths
TEST_NAMES = [
    "JEFFREY EPSTEIN",  # ~271px with Times
    "GHISLAINE MAXWELL",  # ~348px with Times
    "Sarah Kellen",  # ~169px with Times
    "Bill Clinton",  # ~154px with Times
]

# Load and calibrate
pages = convert_from_path(FILE_PATH)
img = np.array(pages[0])
img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

# Get calibration data from OCR
data = pytesseract.image_to_data(img_bgr, output_type=pytesseract.Output.DICT)
target_box = None
for i, text in enumerate(data['text']):
    if CONTROL_WORD.lower() in text.lower():
        target_box = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
        break

control_width_px = target_box[2]
print(f"Calibration: '{CONTROL_WORD}' is {control_width_px}px wide in the document")

# Find some redaction blocks to test against
gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

redactions = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if w > 30 and h > 10 and w/h > 1.5:
        redactions.append((x, y, w, h))
redactions.sort(key=lambda b: b[1])

# Pick a few redactions of different sizes to test
test_redactions = [
    (282, "Block #5"),  # Should be close to "JEFFREY EPSTEIN" (~271px with Times)
    (400, "Block #2"),  # Large block
    (107, "Block #1"),  # Small block
]

# Get all font files
font_files = [f for f in os.listdir(FONTS_DIR) if f.endswith('.ttf') or f.endswith('.TTF')]
print(f"\nTesting {len(font_files)} fonts...\n")
print("="*100)

results = []

for font_file in sorted(font_files):
    font_path = os.path.join(FONTS_DIR, font_file)
    try:
        font = ImageFont.truetype(font_path, 12)

        # Calculate scale factor
        control_width_theoretical = font.getlength(CONTROL_WORD)
        scale_factor = control_width_px / control_width_theoretical

        # Test each redaction
        total_error = 0
        tests = 0

        for redaction_width, redaction_name in test_redactions:
            for name in TEST_NAMES:
                predicted = font.getlength(name) * scale_factor
                error = abs(predicted - redaction_width)
                total_error += error
                tests += 1

        avg_error = total_error / tests
        results.append((font_file, avg_error))

    except Exception as e:
        pass

# Sort by average error (lower is better)
results.sort(key=lambda x: x[1])

print(f"\n{'Font File':<30} {'Average Error (px)':>20} {'Ranking'}")
print("-"*100)

for i, (font_file, avg_error) in enumerate(results[:10]):
    medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"#{i+1}"
    print(f"{font_file:<30} {avg_error:>20.2f}       {medal}")

if results:
    best_font = results[0][0]
    print(f"\n{'='*100}")
    print(f"RECOMMENDED FONT: {best_font}")
    print(f"Average error: {results[0][1]:.2f}px per prediction")
    print(f"{'='*100}")
