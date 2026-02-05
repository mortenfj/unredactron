#!/usr/bin/env python3
"""
Top 10 UNIQUE Redaction Detections - Summary Report
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import ImageFont

FILE_PATH = "files/EFTA00037366.pdf"
FONT_PATH = "fonts/fonts/times.ttf"

# Comprehensive candidate list
CANDIDATES = [
    "Sarah", "Kellen", "Ghislaine", "Nadia", "Lesley", "Jennifer", "Jessica",
    "Jeffrey", "Epstein", "Bill", "Clinton", "Hammond", "Prince", "Andrew",
    "Emmy", "Taylor", "Brunel", "Maxwell", "Jean-Luc", "Nicole", "Melissa",
    "Kimberly", "Stephanie", "Emily", "Ashley", "Amanda", "Mary", "Anne",
    "Marie", "Maria", "Elena", "Jo", "Beth", "Jane", "Louise", "Margaret",
    "Robert", "John", "Michael", "David", "Richard", "Joseph", "Thomas",
    "Charles", "William", "Daniel", "Mark", "Donald", "Steven", "Paul",
    "Sarah Kellen", "Anne Marie", "Maria Elena", "Mary Anne", "Mary Beth",
    "Jo Ann", "Mary Jane", "Mary Louise", "Mary Margaret", "Mary Kay",
    "Ghislaine Maxwell", "Prince Andrew", "Bill Clinton", "Jean-Luc Brunel",
]

print("="*120)
print(" "*40 + "TOP 10 UNIQUE REDACTION DETECTIONS")
print("="*120)

# Load PDF
images = convert_from_path(FILE_PATH, dpi=1200)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

# Load font
font_size = int(12 * 1200 / 72)
font = ImageFont.truetype(FONT_PATH, font_size)

# Find redactions
_, black_mask = cv2.threshold(gray, 5, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

redactions = [(x, y, w, h) for cnt in contours for x, y, w, h in [cv2.boundingRect(cnt)] if w > 200 and h > 100]

# Analyze and find best match for each redaction
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

# Display top 10 unique redactions
print(f"\nRank  {'Detected Name':<30} {'Position':<18} {'Size':<12} {'Width':<12} {'Diff':<10} {'Error':<8} {'Letters'}")
print("-"*120)

for i, match in enumerate(best_matches[:10], 1):
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

    print(f"{i:<5} {match['candidate']:<30} {pos_str:<18} {size_str:<12} "
          f"{match['expected']:>8.1f}px  {match['diff']:>6.1f}px   "
          f"{match['error']:>5.1f}%   {match['letters']:>3}  {rating}")

print("="*120)
print(f"SUMMARY: Found {len(best_matches)} redactions with matches within 30% tolerance")
print(f"         Perfect matches (<1%): {sum(1 for m in best_matches if m['error'] < 1)}")
print(f"         Excellent matches (<5%): {sum(1 for m in best_matches if m['error'] < 5)}")
print(f"         Good matches (<10%): {sum(1 for m in best_matches if m['error'] < 10)}")
print("="*120)

# Show detailed breakdown of top 5
print(f"\nDETAILED BREAKDOWN - TOP 5:")
print("="*120)

for i, match in enumerate(best_matches[:5], 1):
    print(f"\n#{i} REDACTION AT {match['position']}")
    print(f"  Detected:     '{match['candidate']}'")
    print(f"  Size:         {match['size'][0]}x{match['size'][1]}px")
    print(f"  Width match:  {match['expected']:.1f}px expected vs {match['actual']:.1f}px actual")
    print(f"  Difference:   {match['diff']:.1f}px ({match['error']:.2f}%)")
    print(f"  Letters:      {match['letters']}")

    # Letter-by-letter breakdown
    print(f"  Letter breakdown: ", end="")
    for char in match['candidate']:
        if char == " ":
            print(f"' '(space:5px) ", end="")
        else:
            width = font.getlength(char)
            print(f"'{char}':{width:.1f}px ", end="")
    print()

print("="*120)
