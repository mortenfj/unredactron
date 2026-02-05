#!/usr/bin/env python3
"""
Brute Force Analysis - Calculate min/max letter bounds and test all possibilities
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import ImageFont
import itertools

FILE_PATH = "files/EFTA00037366.pdf"
FONT_PATH = "fonts/fonts/times.ttf"
TARGET_W = 962  # Redaction width in pixels

print("="*100)
print("BRUTE FORCE ANALYSIS - Letter Width Bounds")
print("="*100)

# Load font at 1200 DPI
font_size = int(12 * 1200 / 72)
font = ImageFont.truetype(FONT_PATH, font_size)

# Measure ALL letters (uppercase and lowercase)
print(f"\n[STEP 1] Measuring all letter widths at 1200 DPI...")
print(f"Font: Times New Roman, {font_size/1200*72:.0f}pt")
print(f"{'Letter':<10} {'Width (px)':<15} {'Type'}")
print("-"*50)

letter_widths = {}
for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz":
    width = font.getlength(char)
    char_type = "UPPER" if char.isupper() else "lower"
    letter_widths[char] = width
    marker = "  ← NARROWEST" if width == min(font.getlength(c) for c in letter_widths) else ""
    marker = "  ← WIDEST" if width == max(font.getlength(c) for c in letter_widths) else marker
    print(f"{char:<10} {width:>10.1f}px   {char_type}{marker}")

# Find narrowest and widest
narrowest = min(letter_widths, key=letter_widths.get)
widest = max(letter_widths, key=letter_widths.get)

print(f"\nNarrowest letter: '{narrowest}' at {letter_widths[narrowest]:.1f}px")
print(f"Widest letter: '{widest}' at {letter_widths[widest]:.1f}px")

# Calculate letter count bounds
print(f"\n[STEP 2] Calculating letter count bounds...")
print(f"Redaction width: {TARGET_W}px")

# Account for spacing between letters (approx 5px per gap at 1200 DPI)
spacing_per_letter = 5

# Min letters = all widest letters
min_letters_possible = int(TARGET_W / (letter_widths[widest] + spacing_per_letter))
# Max letters = all narrowest letters
max_letters_possible = int(TARGET_W / (letter_widths[narrowest] + spacing_per_letter))

print(f"\nIf ALL letters were '{widest}' (widest): {min_letters_possible} letters max")
print(f"If ALL letters were '{narrowest}' (narrowest): {max_letters_possible} letters max")
print(f"\nPossible letter count: {min_letters_possible} to {max_letters_possible} letters")

# More realistic bounds using average letter width
avg_width = sum(letter_widths.values()) / len(letter_widths)
realistic_min = int(TARGET_W / (avg_width + spacing_per_letter)) - 2
realistic_max = int(TARGET_W / (avg_width + spacing_per_letter)) + 2

print(f"Realistic range (using average letter width): {realistic_min} to {realistic_max} letters")

# Now test candidates
print(f"\n[STEP 3] Testing candidate names...")

CANDIDATES = [
    "Sarah",
    "Kellen",
    "Ghislaine",
    "Nadia",
    "Lesley",
    "Jeffrey",
    "Epstein",
    "Bill",
    "Clinton",
    "Hammond",
    "Prince",
    "Andrew",
    "Emmy",
    "Taylor",
    "Brunel",
    "Maxwell",
    "Jean-Luc",
    "Sarah Kellen",
]

print(f"\nTesting {len(CANDIDATES)} candidates:")
print(f"{'Name':<20} {'Width':<10} {'Letters':<10} {'Avg Width':<12} {'Diff':<10} {'Error':<10} {'In Range'}")
print("-"*100)

valid_candidates = []
for name in CANDIDATES:
    expected_width = font.getlength(name)
    num_letters = len(name.replace(" ", ""))  # Exclude spaces from letter count
    avg_letter_width = expected_width / num_letters if num_letters > 0 else 0
    diff = abs(expected_width - TARGET_W)
    pct_error = diff / expected_width * 100

    # Check if letter count is in realistic range
    in_range = "✓" if realistic_min <= num_letters <= realistic_max else "✗"
    if in_range == "✓" and pct_error < 20:
        valid_candidates.append((name, expected_width, diff, pct_error))

    print(f"{name:<20} {expected_width:>8.1f}px  {num_letters:>6}      {avg_letter_width:>6.1f}px     {diff:>6.1f}px   {pct_error:>5.1f}%    {in_range}")

print(f"\n[STEP 4] Analyzing letter composition of valid candidates...")

if valid_candidates:
    print(f"\n{len(valid_candidates)} candidates within realistic letter count range:")
    print(f"{'Name':<20} {'Letters':<10} {'First':<10} {'Last':<10} {'Width Match'}")
    print("-"*80)

    for name, exp_width, diff, pct in sorted(valid_candidates, key=lambda x: x[3]):
        first = name[0]
        last = name[-1]
        first_width = letter_widths.get(first, 0)
        last_width = letter_widths.get(last, 0)
        match_quality = "★ EXCELLENT" if pct < 8 else "→ GOOD" if pct < 15 else "✗ FAIR"
        print(f"{name:<20} {len(name.replace(' ', '')):>6}       '{first}' ({first_width:>5.1f}px)  '{last}' ({last_width:>5.1f}px)  {pct:>5.1f}% - {match_quality}")

        # Show letter-by-letter breakdown
        print(f"  Letter breakdown: ", end="")
        total = 0
        for i, char in enumerate(name):
            if char == " ":
                char_width = spacing_per_letter  # Space
            else:
                char_width = letter_widths.get(char, 0)
            total += char_width
            print(f"'{char}':{char_width:.1f}px ", end="")
        print(f"\n  Calculated total: {total:.1f}px")
        print()

# Brute force: Test all combinations of common first names
print(f"\n[STEP 5] Brute force testing common first names...")

COMMON_FIRST_NAMES = [
    "Sarah", "Kellen", "Ghislaine", "Nadia", "Lesley", "Jennifer", "Jessica",
    "Emily", "Ashley", "Amanda", "Stephanie", "Nicole", "Melissa", "Kimberly",
    "Jeffrey", "William", "Robert", "John", "Michael", "David", "Richard",
    "Joseph", "Thomas", "Charles", "Hammond", "Emmy", "Taylor", "Maxwell",
]

print(f"\nTesting {len(COMMON_FIRST_NAMES)} common first names...")

best_matches = []
for name in COMMON_FIRST_NAMES:
    expected_width = font.getlength(name)
    diff = abs(expected_width - TARGET_W)
    pct_error = diff / expected_width * 100

    if pct_error < 20:  # Within 20%
        best_matches.append((name, expected_width, diff, pct_error))

best_matches.sort(key=lambda x: x[3])  # Sort by error percentage

print(f"\n{len(best_matches)} matches within 20%:")
print(f"{'Name':<20} {'Width':<10} {'Diff':<10} {'Error':<10} {'Match'}")
print("-"*70)

for name, exp_width, diff, pct in best_matches[:10]:  # Top 10
    match = "★★★" if pct < 5 else "★★" if pct < 10 else "★" if pct < 15 else "→"
    print(f"{name:<20} {exp_width:>8.1f}px  {diff:>6.1f}px  {pct:>5.1f}%    {match}")

print(f"\n{'='*100}")
print(f"CONCLUSION:")
print(f"  Redaction width: {TARGET_W}px")
print(f"  Possible letters: {realistic_min} to {realistic_max}")
print(f"  Best match: {best_matches[0][0] if best_matches else 'None found'} ({best_matches[0][3]:.1f}% error)" if best_matches else "")
print(f"{'='*100}")
