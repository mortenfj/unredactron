#!/usr/bin/env python3
"""
TRUE BRUTE FORCE - Test all 351 names from names.csv against redactions
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import ImageFont

FILE_PATH = "files/EFTA00037366.pdf"
FONT_PATH = "fonts/fonts/times.ttf"

# Load names from the cleaned list
with open('names_clean.txt', 'r') as f:
    CANDIDATES = [line.strip() for line in f if line.strip()]

print("="*120)
print(f"TRUE BRUTE FORCE - Testing {len(CANDIDATES)} names from names.csv")
print("="*120)

# Load PDF
print(f"\nLoading PDF at 1200 DPI...")
images = convert_from_path(FILE_PATH, dpi=1200)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

# Load font
font_size = int(12 * 1200 / 72)
font = ImageFont.truetype(FONT_PATH, font_size)

# Find redactions
print(f"Finding redactions...")
_, black_mask = cv2.threshold(gray, 5, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

redactions = [(x, y, w, h) for cnt in contours for x, y, w, h in [cv2.boundingRect(cnt)] if w > 200 and h > 100]

print(f"Found {len(redactions)} significant redactions")
print(f"Testing {len(redactions)} × {len(CANDIDATES)} = {len(redactions) * len(CANDIDATES):,} combinations\n")

# Analyze each redaction
best_matches = []
for i, (x, y, w, h) in enumerate(redactions):
    best_candidate = None
    best_error = 100

    for candidate in CANDIDATES:
        expected_width = font.getlength(candidate)
        diff = abs(expected_width - w)
        pct_error = diff / expected_width * 100 if expected_width > 0 else 100

        if pct_error < best_error:
            best_error = pct_error
            best_candidate = candidate
            best_expected = expected_width
            best_diff = diff

    if best_error < 30:  # Only keep reasonable matches
        best_matches.append({
            'rank': i + 1,
            'position': (x, y),
            'size': (w, h),
            'candidate': best_candidate,
            'expected': best_expected,
            'actual': w,
            'diff': best_diff,
            'error': best_error,
            'letters': len(best_candidate.replace(" ", ""))
        })

# Sort by error percentage
best_matches.sort(key=lambda m: m['error'])

# Display top matches
print(f"{'='*120}")
print(f"TOP 20 UNIQUE REDACTIONS (brute forced against {len(CANDIDATES)} names)")
print(f"{'='*120}")
print(f"\nRank  {'Detected Name':<35} {'Position':<18} {'Size':<12} {'Width':<12} {'Diff':<10} {'Error':<8} {'Letters'}")
print("-"*130)

for i, match in enumerate(best_matches[:20], 1):
    pos_str = f"({match['position'][0]}, {match['position'][1]})"
    size_str = f"{match['size'][0]}x{match['size'][1]}"

    # Rating
    if match['error'] < 1:
        rating = "★★★"
    elif match['error'] < 5:
        rating = "★★"
    elif match['error'] < 10:
        rating = "★"
    else:
        rating = ""

    print(f"{i:<5} {match['candidate']:<35} {pos_str:<18} {size_str:<12} "
          f"{match['expected']:>8.1f}px  {match['diff']:>6.1f}px   "
          f"{match['error']:>5.1f}%   {match['letters']:>3}  {rating}")

print("="*120)
print(f"SUMMARY:")
print(f"  Total matches found: {len(best_matches)}")
print(f"  Perfect matches (<1%): {sum(1 for m in best_matches if m['error'] < 1)}")
print(f"  Excellent matches (<5%): {sum(1 for m in best_matches if m['error'] < 5)}")
print(f"  Good matches (<10%): {sum(1 for m in best_matches if m['error'] < 10)}")
print("="*120)

# Check for Marcinkova specifically
print(f"\nSearching for 'Marcinkova' in results...")
for match in best_matches:
    if 'Marcinkova' in match['candidate'] or 'marcinko' in match['candidate'].lower():
        print(f"  Found: {match['candidate']} at {match['position']} - {match['error']:.2f}% error")

print("="*120)
