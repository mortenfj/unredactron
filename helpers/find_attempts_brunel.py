#!/usr/bin/env python3
"""Find the sentence 'Attempts were made to [REDACTED] and Brunel'"""

import cv2
import numpy as np
from pdf2image import convert_from_path
import pytesseract

FILE_PATH = "files/EFTA00037366.pdf"

# Load at 1200 DPI
images = convert_from_path(FILE_PATH, dpi=1200)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

print("Searching for 'Attempts' and nearby redactions...")

# Get OCR
data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

# Find "Attempts"
attempts_locations = []
for i in range(len(data['text'])):
    text = data['text'][i].strip()
    if 'Attempts' in text and data['conf'][i] > 60:
        x, y = data['left'][i], data['top'][i]
        attempts_locations.append((x, y, data['width'][i], data['height'][i], text))
        print(f"Found 'Attempts' variant: '{text}' at ({x}, {y})")

print(f"\nFound {len(attempts_locations)} 'Attempts' occurrences")

# Find ALL redactions
_, black_mask = cv2.threshold(gray, 5, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

redactions = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if w > 200 and h > 100:
        redactions.append((x, y, w, h))

print(f"\nFound {len(redactions)} significant redactions")

# For each "Attempts", find nearby redactions
for att_x, att_y, att_w, att_h, att_text in attempts_locations:
    print(f"\n{'='*80}")
    print(f"Analyzing: '{att_text}' at ({att_x}, {att_y})")
    print(f"{'='*80}")

    # Look for redactions within 5000 pixels horizontally and 500 vertically
    nearby = []
    for r_x, r_y, r_w, r_h in redactions:
        if abs(r_y - att_y) < 200 and r_x > att_x:
            nearby.append((r_x, r_y, r_w, r_h, r_x - att_x))

    nearby.sort(key=lambda x: x[4])  # Sort by distance

    print(f"\nNearby redactions (to the right):")
    for r_x, r_y, r_w, r_h, dist in nearby[:5]:
        print(f"  Redaction at ({r_x}, {r_y}), size: {r_w}x{r_h}px, distance: {dist}px")

    # Also look for "Brunel" in same area
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        if 'Brunel' in text and data['conf'][i] > 60:
            b_x, b_y = data['left'][i], data['top'][i]
            if abs(b_y - att_y) < 200 and b_x > att_x:
                print(f"\n  ★ Found 'Brunel' at ({b_x}, {b_y})")
                print(f"    Distance from 'Attempts': {b_x - att_x}px")
