#!/usr/bin/env python3
"""
Text Reconstruction from Protrusions - Match detected letter features to words.
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import ImageFont, ImageDraw
import os

FILE_PATH = "files/EFTA00037366.pdf"
FONT_PATH = "fonts/fonts/times.ttf"

print("="*100)
print("TEXT RECONSTRUCTION FROM PROTRUSION PATTERNS")
print("="*100)

# Load document at 1200 DPI
print(f"\nLoading document at 1200 DPI...")
images = convert_from_path(FILE_PATH, dpi=1200)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

# Find redactions
_, black_mask = cv2.threshold(gray, 5, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

redactions = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if 400 < w < 800:  # Focus on name-sized
        redactions.append((x, y, w, h))

# Font for rendering
scaled_font_size = int(12 * 1200 / 72)
font = ImageFont.truetype(FONT_PATH, scaled_font_size)

# Common first names
NAMES = [
    "Sarah", "Kellen", "Ghislaine", "Maxwell", "Nadia", "Marcinkova",
    "Lesley", "Groff", "Jeffrey", "Epstein", "Bill", "Clinton",
    "Prince", "Andrew", "Emmy", "Taylor", "Hammond",
    "John", "Jane", "David", "Michael", "Jennifer"
]

print(f"Testing {len(NAMES)} common names against protrusion patterns...")

for i, (x, y, w, h) in enumerate(redactions[:5]):
    print(f"\n{'='*100}")
    print(f"Redaction #{i+1} at ({x}, {y}), size: {w}x{h}px")
    print(f"{'='*100}")

    # Detect protrusions
    left_start = max(0, x - 15)
    left_end = x
    left_region = gray[y:y+h, left_start:left_end]

    right_start = x + w
    right_end = min(gray.shape[1], x + w + 15)
    right_region = gray[y:y+h, right_start:right_end]

    # Exclude corners
    top_cutoff = int(h * 0.1)
    bottom_cutoff = int(h * 0.9)
    mid_h = bottom_cutoff - top_cutoff

    left_middle = left_region[top_cutoff:bottom_cutoff, :]
    right_middle = right_region[top_cutoff:bottom_cutoff, :]

    # Detect features
    left_features = {'upper': False, 'lower': False, 'count': 0}
    right_features = {'upper': False, 'lower': False, 'count': 0}

    # Analyze left edge
    for col_idx in range(left_middle.shape[1]):
        col = left_middle[:, col_idx]
        dark_rows = np.where(col < 100)[0]

        if len(dark_rows) > 0 and len(dark_rows) < 30:
            position = dark_rows[0]
            left_features['count'] += 1

            if position < mid_h * 0.3:
                left_features['upper'] = True
            elif position > mid_h * 0.7:
                left_features['lower'] = True

    # Analyze right edge
    for col_idx in range(right_middle.shape[1]):
        col = right_middle[:, col_idx]
        dark_rows = np.where(col < 100)[0]

        if len(dark_rows) > 0 and len(dark_rows) < 30:
            position = dark_rows[0]
            right_features['count'] += 1

            if position < mid_h * 0.3:
                right_features['upper'] = True
            elif position > mid_h * 0.7:
                right_features['lower'] = True

    print(f"\nDetected features:")
    print(f"  Left edge:  upper={left_features['upper']}, lower={left_features['lower']}, protrusions={left_features['count']}")
    print(f"  Right edge: upper={right_features['upper']}, lower={right_features['lower']}, protrusions={right_features['count']}")

    # Match names against these features
    print(f"\nMatching names...")

    for name in NAMES:
        # Calculate expected width
        expected_width = font.getlength(name)

        # Check width match
        width_diff = abs(expected_width - w)
        width_match = width_diff < expected_width * 0.15  # Within 15%

        # Analyze name features
        name_has_upper = any(c in 'bdfhklt' for c in name)
        name_has_lower = any(c in 'gjpqy' for c in name)

        # First letter
        if len(name) > 0:
            first_has_upper = name[0] in 'bdfhklt'
            first_has_lower = name[0] in 'gjpqy'

        # Last letter
        if len(name) > 0:
            last_has_upper = name[-1] in 'bdfhklt'
            last_has_lower = name[-1] in 'gjpqy'

        # Check if features match
        left_match = True
        if left_features['count'] > 0:
            if left_features['upper'] and not first_has_upper:
                left_match = False
            if left_features['lower'] and not first_has_lower:
                left_match = False

        right_match = True
        if right_features['count'] > 0:
            if right_features['upper'] and not last_has_upper:
                right_match = False
            if right_features['lower'] and not last_has_lower:
                right_match = False

        if width_match and left_match and right_match:
            score = 100
            if left_features['count'] > 0:
                if ((left_features['upper'] and first_has_upper) or
                    (left_features['lower'] and first_has_lower)):
                    score += 20

            if right_features['count'] > 0:
                if ((right_features['upper'] and last_has_upper) or
                    (right_features['lower'] and last_has_lower)):
                    score += 20

            print(f"  ★ '{name}' - Width: {expected_width:.0f}px (actual: {w}px), Score: {score}")

print(f"\n{'='*100}")
print(f"RECONSTRUCTION COMPLETE")
print(f"{'='*100}")
