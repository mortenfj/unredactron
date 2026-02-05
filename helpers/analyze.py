#!/usr/bin/env python3
"""
Complete analysis: Auto-detect font, then analyze redactions.
"""

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from PIL import ImageFont
import os

FILE_PATH = "files/EFTA00037366.pdf"
FONTS_DIR = "fonts/fonts/"

# Suspect names to test
SUSPECT_LIST = [
    "Sarah Kellen", "Ghislaine Maxwell", "Nadia Marcinkova",
    "Lesley Groff", "Bill Hammond", "Jeffrey Epstein",
    "Bill Clinton", "Prince Andrew", "Emmy Taylor"
]

print("="*100)
print("COMPLETE REDACTION ANALYSIS")
print("="*100)

# Load document
pages = convert_from_path(FILE_PATH)
img = np.array(pages[0])
img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

print(f"\n[STEP 1] Auto-detecting font...")

# Get OCR data
data = pytesseract.image_to_data(img_bgr, output_type=pytesseract.Output.DICT)

# Collect visible text measurements
visible_text = []
for i in range(len(data['text'])):
    conf = int(data['conf'][i]) if data['conf'][i] != '-1' else 0
    text = data['text'][i].strip()
    w = data['width'][i]

    if conf > 85 and 4 <= len(text) <= 20 and w > 30:
        visible_text.append((text, w))

# Test Times New Roman at different sizes
best_size = 12
best_consistency = 999
best_scale = 2.7

for font_size in [8, 9, 10, 11, 12, 13, 14]:
    try:
        font = ImageFont.truetype(os.path.join(FONTS_DIR, "times.ttf"), font_size)
        scale_factors = []

        for text, actual_width in visible_text:
            theoretical = font.getlength(text)
            if theoretical > 0:
                scale_factors.append(actual_width / theoretical)

        if len(scale_factors) >= 5:
            avg = sum(scale_factors) / len(scale_factors)
            std = (sum((x - avg) ** 2 for x in scale_factors) / len(scale_factors)) ** 0.5
            consistency = (std / avg) * 100

            if consistency < best_consistency:
                best_consistency = consistency
                best_size = font_size
                best_scale = avg
    except:
        pass

print(f"  ✓ Detected: Times New Roman at {best_size}pt")
print(f"  ✓ Scale factor: {best_scale:.4f}")
print(f"  ✓ Consistency: {best_consistency:.2f}%")

print(f"\n[STEP 2] Finding redactions...")

# Find redactions
gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

redactions = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if w > 30 and h > 10 and w/h > 1.5:
        redactions.append((x, y, w, h))

print(f"  ✓ Found {len(redactions)} redaction blocks")

print(f"\n[STEP 3] Testing {len(SUSPECT_LIST)} suspect names...")

font = ImageFont.truetype(os.path.join(FONTS_DIR, "times.ttf"), best_size)

matches = []
for x, y, w, h in redactions:
    for name in SUSPECT_LIST:
        for variant in [name, name.upper()]:
            predicted = font.getlength(variant) * best_scale
            diff = abs(predicted - w)

            if diff <= 15:
                matches.append({
                    'x': x,
                    'y': y,
                    'w': w,
                    'h': h,
                    'name': variant,
                    'predicted': predicted,
                    'diff': diff
                })

print(f"\n{'='*100}")
print(f"RESULTS: Found {len(matches)} potential matches")
print(f"{'='*100}")

if matches:
    # Group by width
    by_width = {}
    for m in matches:
        w = m['w']
        if w not in by_width:
            by_width[w] = []
        by_width[w].append(m)

    print(f"\n{'Redaction Width':<20} {'Count':<10} {'Potential Matches'}")
    print("-"*100)

    for width in sorted(by_width.keys()):
        matches_at_width = by_width[width]
        names = sorted(set(m['name'] for m in matches_at_width))

        # Find best match (lowest diff)
        best = min(matches_at_width, key=lambda x: x['diff'])

        print(f"{width}px ({len(matches_at_width)} matches)      {', '.join(names)}")
        if len(names) == 1:
            print(f"  └─ Best: '{best['name']}' (predicted: {best['predicted']:.1f}px, diff: {best['diff']:+.1f}px)")

    # Frequency table
    print(f"\n{'='*100}")
    print("MATCH FREQUENCY")
    print("="*100)

    name_counts = {}
    for m in matches:
        name = m['name']
        name_counts[name] = name_counts.get(name, 0) + 1

    for name, count in sorted(name_counts.items(), key=lambda x: -x[1]):
        print(f"  {name}: {count} occurrence(s)")

else:
    print("  No matches found within 15px tolerance")

print(f"\n{'='*100}")
