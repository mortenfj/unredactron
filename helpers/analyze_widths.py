#!/usr/bin/env python3
"""
Analyze all redaction widths across all pages to find patterns.
Cluster by size to identify common redaction types (names, dates, etc.)
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
from collections import Counter

FILE_PATH = "files/EFTA00513855.pdf"

def find_redactions(image_cv):
    """Locates black bars using Computer Vision contours."""
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    redactions = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 30 and h > 10 and w/h > 1.5:
            redactions.append((x, y, w, h))
    return redactions

print(f"Loading {FILE_PATH}...")
pages = convert_from_path(FILE_PATH)
print(f"Loaded {len(pages)} pages\n")

all_widths = []
all_redactions = []

for i, page in enumerate(pages):
    img = np.array(page)
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    redactions = find_redactions(img_bgr)

    for (x, y, w, h) in redactions:
        all_widths.append(w)
        all_redactions.append((i+1, x, y, w, h))

print(f"Total redactions found: {len(all_widths)}")
print("="*100)

# Cluster widths (round to nearest 5px to group similar sizes)
width_clusters = {}
for w in all_widths:
    cluster_key = round(w / 5) * 5
    width_clusters[cluster_key] = width_clusters.get(cluster_key, 0) + 1

print("\nREDACTION WIDTH CLUSTERS (grouped by 5px)")
print("-"*100)
print(f"{'Width Range (px)':<20} {'Count':<10} {'Percentage':<15} {'Possible Content'}")
print("-"*100)

for width in sorted(width_clusters.keys()):
    count = width_clusters[width]
    pct = (count / len(all_widths)) * 100
    range_str = f"{width-2} - {width+2}"

    # Guess content type based on width
    if width < 80:
        content = "Short (initials, dates, numbers)"
    elif width < 150:
        content = "Medium (short names, single words)"
    elif width < 250:
        content = "Name (First Last)"
    elif width < 350:
        content = "Long name / Uppercase name"
    elif width < 500:
        content = "Multiple names / phrases"
    else:
        content = "Very long (addresses, paragraphs)"

    print(f"{range_str:<20} {count:<10} {pct:<14.1f}% {content}")

# Show exact width distribution for the most common clusters
print("\n" + "="*100)
print("TOP 10 MOST COMMON EXACT WIDTHS")
print("="*100)

width_counter = Counter([w for w in all_widths])
for width, count in width_counter.most_common(10):
    pct = (count / len(all_widths)) * 100
    print(f"  {width:3d}px: {count:3d} occurrences ({pct:5.1f}%)")

# Test our suspect names against the most common widths
print("\n" + "="*100)
print("TESTING SUSPECT NAMES AGAINST MOST COMMON WIDTHS")
print("="*100)

from PIL import ImageFont

# Calibrate with page 1
img = np.array(pages[0])
img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
import pytesseract
data = pytesseract.image_to_data(img_bgr, output_type=pytesseract.Output.DICT)
target_box = None
for i, text in enumerate(data['text']):
    if "Contacts" in text:
        target_box = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
        break

font = ImageFont.truetype("fonts/fonts/times.ttf", 12)
scale_factor = target_box[2] / font.getlength("Contacts")

SUSPECT_NAMES = [
    "Sarah Kellen", "Ghislaine Maxwell", "Nadia Marcinkova",
    "Lesley Groff", "Bill Hammond", "Jeffrey Epstein",
    "Bill Clinton", "Prince Andrew", "Emmy Taylor"
]

print(f"\nCalibration scale factor: {scale_factor:.4f}")
print(f"Tolerance: 15px (relaxed from 3px)\n")

top_widths = [w for w, c in width_counter.most_common(10)]

for redaction_width in top_widths:
    count = width_counter[redaction_width]
    print(f"\n--- Width: {redaction_width}px ({count} occurrences) ---")

    matches = []
    for name in SUSPECT_NAMES:
        for variant in [name, name.upper()]:
            predicted = font.getlength(variant) * scale_factor
            diff = abs(predicted - redaction_width)

            if diff <= 15:  # Relaxed tolerance
                matches.append((variant, diff, predicted))

    if matches:
        matches.sort(key=lambda x: x[1])
        for variant, diff, predicted in matches:
            print(f"  ✓ '{variant}' (predicted: {predicted:.1f}px, diff: {diff:+.1f}px)")
    else:
        closest = None
        closest_diff = 999
        for name in SUSPECT_NAMES:
            for variant in [name, name.upper()]:
                predicted = font.getlength(variant) * scale_factor
                diff = abs(predicted - redaction_width)
                if diff < closest_diff:
                    closest_diff = diff
                    closest = (variant, predicted)
        print(f"  (No matches within 15px - closest: '{closest[0]}' at {closest[1]:.1f}px, diff {closest_diff:+.1f}px)")
