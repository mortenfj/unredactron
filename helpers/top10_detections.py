#!/usr/bin/env python3
"""
Find the TOP 10 redaction detections across the entire document
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import ImageFont
import pytesseract

FILE_PATH = "files/EFTA00037366.pdf"
FONT_PATH = "fonts/fonts/times.ttf"

# Comprehensive candidate list
CANDIDATES = [
    # Single names
    "Sarah", "Kellen", "Ghislaine", "Nadia", "Lesley", "Jennifer", "Jessica",
    "Jeffrey", "Epstein", "Bill", "Clinton", "Hammond", "Prince", "Andrew",
    "Emmy", "Taylor", "Brunel", "Maxwell", "Jean-Luc", "Nicole", "Melissa",
    "Kimberly", "Stephanie", "Emily", "Ashley", "Amanda", "Mary", "Anne",
    "Marie", "Maria", "Elena", "Jo", "Beth", "Jane", "Louise", "Margaret",
    "Robert", "John", "Michael", "David", "Richard", "Joseph", "Thomas",
    "Charles", "William", "Daniel", "Mark", "Donald", "Steven", "Paul",

    # Double names
    "Sarah Kellen", "Anne Marie", "Maria Elena", "Mary Anne", "Mary Beth",
    "Anne Marie", "Jo Ann", "Mary Jane", "Mary Louise", "Mary Margaret",
    "Jean-Luc", "Mary Kay",

    # Common phrases
    "Epstein", "Maxwell", "Ghislaine Maxwell", "Sarah Kellen",
    "Prince Andrew", "Bill Clinton", "Jean-Luc Brunel",
]

print("="*100)
print("TOP 10 REDACTION DETECTIONS - Comprehensive Analysis")
print("="*100)

# Load PDF
print(f"\nLoading PDF at 1200 DPI...")
images = convert_from_path(FILE_PATH, dpi=1200)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

# Load font
font_size = int(12 * 1200 / 72)
font = ImageFont.truetype(FONT_PATH, font_size)

# Find all redactions
print(f"Finding redactions...")
_, black_mask = cv2.threshold(gray, 5, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

redactions = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if w > 200 and h > 100:  # Only significant redactions
        redactions.append((x, y, w, h))

print(f"Found {len(redactions)} significant redactions")

# Analyze each redaction
print(f"\nAnalyzing {len(redactions)} redactions against {len(CANDIDATES)} candidates...")
print(f"{'='*100}")

all_matches = []

for i, (x, y, w, h) in enumerate(redactions):
    # Test each candidate
    for candidate in CANDIDATES:
        expected_width = font.getlength(candidate)
        diff = abs(expected_width - w)
        pct_error = diff / expected_width * 100 if expected_width > 0 else 100

        # Calculate match score (inverse of error percentage, capped at 100)
        width_score = max(0, 100 - pct_error)

        # Only keep matches within 30% error
        if pct_error < 30:
            all_matches.append({
                'redaction_id': i,
                'position': (x, y),
                'size': (w, h),
                'candidate': candidate,
                'expected_width': expected_width,
                'actual_width': w,
                'diff': diff,
                'pct_error': pct_error,
                'width_score': width_score,
                'letters': len(candidate.replace(" ", ""))
            })

# Sort by percentage error (ascending)
all_matches.sort(key=lambda m: m['pct_error'])

# Show top 10
print(f"\nTOP 10 BEST MATCHES:")
print(f"{'Rank':<6} {'Candidate':<25} {'Position':<15} {'Size':<12} {'Width':<12} {'Diff':<10} {'Error':<10} {'Score'}")
print("-"*120)

for rank, match in enumerate(all_matches[:10], 1):
    pos_str = f"({match['position'][0]}, {match['position'][1]})"
    size_str = f"{match['size'][0]}x{match['size'][1]}"
    width_str = f"{match['expected_width']:.1f}px"

    # Rating
    if match['pct_error'] < 1:
        rating = "★★★"
    elif match['pct_error'] < 5:
        rating = "★★"
    elif match['pct_error'] < 10:
        rating = "★"
    else:
        rating = "→"

    print(f"{rank:<6} {match['candidate']:<25} {pos_str:<15} {size_str:<12} {width_str:<12} "
          f"{match['diff']:>5.1f}px   {match['pct_error']:>5.1f}%     {match['width_score']:>5.1f} {rating}")

print(f"\n{'='*100}")
print(f"SUMMARY:")
print(f"  Total matches found: {len(all_matches)}")
print(f"  Matches within 1%: {sum(1 for m in all_matches if m['pct_error'] < 1)}")
print(f"  Matches within 5%: {sum(1 for m in all_matches if m['pct_error'] < 5)}")
print(f"  Matches within 10%: {sum(1 for m in all_matches if m['pct_error'] < 10)}")
print(f"  Matches within 20%: {sum(1 for m in all_matches if m['pct_error'] < 20)}")
print(f"{'='*100}")

# Also show unique redactions detected
print(f"\nUNIQUE REDACTIONS DETECTED (by position):")
print(f"{'Position':<15} {'Size':<12} {'Best Match':<25} {'Error':<10} {'Letters'}")
print("-"*90)

# Group by redaction ID
by_redaction = {}
for match in all_matches:
    rid = match['redaction_id']
    if rid not in by_redaction or match['pct_error'] < by_redaction[rid]['pct_error']:
        by_redaction[rid] = match

# Sort by error
sorted_redactions = sorted(by_redaction.values(), key=lambda m: m['pct_error'])

for match in sorted_redactions[:15]:
    pos_str = f"({match['position'][0]}, {match['position'][1]})"
    size_str = f"{match['size'][0]}x{match['size'][1]}"
    print(f"{pos_str:<15} {size_str:<12} {match['candidate']:<25} {match['pct_error']:>5.1f}%      "
          f"{match['letters']:>3}")

print(f"\n{'='*100}")
