#!/usr/bin/env python3
"""
Debug script to see predicted widths vs actual widths for each redaction.
"""

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from PIL import ImageFont, ImageDraw, Image

FILE_PATH = "files/EFTA00513855.pdf"
FONT_PATH = "fonts/fonts/times.ttf"
CONTROL_WORD = "Contacts"
SUSPECT_LIST = [
    "Sarah Kellen", "Ghislaine Maxwell", "Nadia Marcinkova",
    "Lesley Groff", "Bill Hammond", "Jeffrey Epstein",
    "Bill Clinton", "Prince Andrew", "Emmy Taylor"
]

print("="*70)
print("WIDTH ANALYSIS - Predicted vs Actual")
print("="*70)

# Load and calibrate
pages = convert_from_path(FILE_PATH)
img = np.array(pages[0])
img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

# Load font
font = ImageFont.truetype(FONT_PATH, 12)

# Calibrate
data = pytesseract.image_to_data(img_bgr, output_type=pytesseract.Output.DICT)
target_box = None
for i, text in enumerate(data['text']):
    if CONTROL_WORD.lower() in text.lower():
        target_box = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
        break

real_width = target_box[2]
base_len = font.getlength(CONTROL_WORD)
scale_factor = real_width / base_len

print(f"\nCalibration:")
print(f"  Control word: '{CONTROL_WORD}'")
print(f"  Actual OCR width: {real_width}px")
print(f"  Theoretical font width: {base_len:.2f}px")
print(f"  Scale factor: {scale_factor:.4f}")

# Find redactions
gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

redactions = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if w > 30 and h > 10 and w/h > 1.5:
        redactions.append((x, y, w, h))
redactions.sort(key=lambda b: b[1])

print(f"\nFound {len(redactions)} redaction blocks on page 1")
print("\n" + "="*70)
print("ANALYZING EACH REDACTION BLOCK")
print("="*70)

for i, (x, y, w, h) in enumerate(redactions):
    print(f"\n--- Block #{i+1} (width: {w}px) ---")
    print(f"{'Name':<30} {'Predicted':>12} {'Actual':>10} {'Diff':>10} {'Status'}")
    print("-"*70)

    closest = None
    closest_diff = 9999

    for name in SUSPECT_LIST:
        for variant in [name, name.upper()]:
            base_width = font.getlength(variant)
            predicted_width = base_width * scale_factor
            diff = abs(predicted_width - w)

            if diff < closest_diff:
                closest_diff = diff
                closest = (variant, predicted_width)

            status = "MATCH" if diff <= 3.0 else f"{diff:+.1f}px"
            print(f"{variant:<30} {predicted_width:>10.1f}px   {w:>6}px     {diff:>+6.1f}px  {status}")

    print(f"\n  Closest: '{closest[0]}' at {closest[1]:.1f}px (diff: {closest_diff:+.1f}px)")

print("\n" + "="*70)
