#!/usr/bin/env python3
"""
Find the actual "with [Kellen] last night" redaction by coordinate matching.
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
import pytesseract
import os

FILE_PATH = "files/EFTA00037366.pdf"
OUTPUT_DIR = "find_kellen"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("="*100)
print("FINDING 'with [Kellen] last night' REDACTION")
print("="*100)

# Load document
images = convert_from_path(FILE_PATH, dpi=1200)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

# Get OCR data to find "with" and "last night"
print(f"\n[STEP 1] Finding 'with' and 'last night' in document...")
data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

with_pos = None
last_pos = None
night_pos = None

for i in range(len(data['text'])):
    text = data['text'][i].strip()
    if 'with' == text.lower() and data['conf'][i] > 80:
        with_pos = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
    elif 'last' == text.lower() and data['conf'][i] > 80:
        last_pos = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
    elif 'night' == text.lower() and data['conf'][i] > 80:
        night_pos = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])

print(f"  'with' found at: {with_pos}")
print(f"  'last' found at: {last_pos}")
print(f"  'night' found at: {night_pos}")

if with_pos and last_pos:
    # Find redactions between "with" and "last"
    print(f"\n[STEP 2] Looking for redactions between x={with_pos[0]} and x={last_pos[0]}...")

    # Find redactions
    _, black_mask = cv2.threshold(gray, 5, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    matching_redactions = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # Check if x position is between "with" and "last"
        if with_pos[0] + with_pos[2] < x < last_pos[0]:
            # Check if y position is close to the text (same line)
            if abs(y - with_pos[1]) < 50:
                matching_redactions.append((x, y, w, h))

    print(f"  Found {len(matching_redactions)} redactions between 'with' and 'last'")

    # Analyze each matching redaction
    print(f"\n[STEP 3] Analyzing candidate redactions...")

    for i, (x, y, w, h) in enumerate(matching_redactions):
        print(f"\n{'='*100}")
        print(f"Redaction at ({x}, {y}), size: {w}x{h}px")
        print(f"{'='*100}")

        # Calculate expected width of "Kellen" at this DPI
        kellen_width = 6 * 85  # Approx 85px per letter at 1200 DPI
        width_diff = abs(w - kellen_width)
        width_match_pct = 100 - (width_diff / kellen_width * 100)

        print(f"  Expected 'Kellen' width: ~{kellen_width}px")
        print(f"  Actual width: {w}px")
        print(f"  Width match: {width_match_pct:.1f}%")

        # Create visualization showing context
        context_x = max(0, with_pos[0] - 100)
        context_y = max(0, y - 50)
        context_w = min(gray.shape[1] - context_x, (last_pos[0] + last_pos[2]) - context_x + 200)
        context_h = min(gray.shape[0] - context_y, 200)

        context_region = gray[context_y:context_y+context_h, context_x:context_x+context_w].copy()
        context_color = cv2.cvtColor(context_region, cv2.COLOR_GRAY2BGR)

        # Draw red box
        box_x = x - context_x
        box_y = y - context_y
        cv2.rectangle(context_color, (box_x, box_y), (box_x + w, box_y + h), (0, 0, 255), 3)

        # Add label
        cv2.putText(context_color, f"Redaction: {w}px wide (Kellen ~{kellen_width}px)",
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imwrite(f"{OUTPUT_DIR}/context_{i+1}.png", context_color)
        print(f"  Saved context visualization: {OUTPUT_DIR}/context_{i+1}.png")

    if len(matching_redactions) == 0:
        print(f"\n  No redactions found between 'with' and 'last' on the same line.")
    elif len(matching_redactions) == 1:
        x, y, w, h = matching_redactions[0]
        kellen_width = 6 * 85
        width_diff = abs(w - kellen_width)
        if width_diff < 50:
            print(f"\n  *** STRONG CANDIDATE: The redaction width ({w}px) closely matches 'Kellen' (~{kellen_width}px) ***")
        else:
            print(f"\n  NOTE: Width match is not exact - could be different name")
    else:
        print(f"\n  Multiple redactions found - need manual inspection")

else:
    print("ERROR: Could not find 'with' or 'last' in document")

print(f"\n{'='*100}")
