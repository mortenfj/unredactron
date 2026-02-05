#!/usr/bin/env python3
"""
Test if the redaction contains TWO names
"Hammond + XXX" or similar combinations
"""

from PIL import ImageFont

FONT_PATH = "fonts/fonts/times.ttf"
TARGET_W = 962  # Redaction width in pixels
SPACING = 5  # Pixels between letters/words

# Load font at 1200 DPI
font_size = int(12 * 1200 / 72)
font = ImageFont.truetype(FONT_PATH, font_size)

# Single names
SINGLE_NAMES = [
    "Hammond", "Sarah", "Kellen", "Ghislaine", "Nadia", "Lesley",
    "Jeffrey", "Epstein", "Bill", "Clinton", "Prince", "Andrew",
    "Emmy", "Taylor", "Brunel", "Maxwell", "Jean-Luc", "Jessica",
    "Jennifer", "Nicole", "Melissa", "Kimberly", "Stephanie",
]

print("="*100)
print("TESTING: Does the 962px redaction contain TWO names?")
print("="*100)

# First, what's the leftover space after "Hammond"?
hammond_width = font.getlength("Hammond")
leftover = TARGET_W - hammond_width - SPACING  # Space between names

print(f"\nHammond width: {hammond_width:.1f}px")
print(f"Redaction width: {TARGET_W}px")
print(f"Leftover space: {leftover:.1f}px (for second name)")

# What fits in that leftover space?
print(f"\n[TEST 1] 'Hammond + XXX' combinations:")
print(f"{'Name':<20} {'Width':<12} {'Hammond + Name':<20} {'Total Width':<15} {'Match'}")
print("-"*90)

for name in SINGLE_NAMES:
    name_width = font.getlength(name)
    combo_width = hammond_width + SPACING + name_width
    diff = abs(combo_width - TARGET_W)
    pct = diff / combo_width * 100

    match = "✓✓✓" if diff < 10 else "✓✓" if diff < 30 else "✓" if diff < 50 else ""
    if match:
        print(f"{name:<20} {name_width:>8.1f}px   Hammond + {name:<13} {combo_width:>10.1f}px      {pct:>5.1f}% {match}")

# Try all pairs
print(f"\n[TEST 2] All possible pairs (in 6-10 letter total range):")
print(f"{'First':<15} {'Second':<15} {'Total Letters':<15} {'Total Width':<15} {'Diff':<10} {'Match'}")
print("-"*100)

best_pairs = []
for name1 in SINGLE_NAMES:
    for name2 in SINGLE_NAMES:
        # Skip same name combinations
        if name1 == name2:
            continue

        letters1 = len(name1)
        letters2 = len(name2)
        total_letters = letters1 + letters2

        # Check letter count range
        if 6 <= total_letters <= 10:
            width1 = font.getlength(name1)
            width2 = font.getlength(name2)
            combo_width = width1 + SPACING + width2

            diff = abs(combo_width - TARGET_W)
            pct = diff / combo_width * 100

            match = "★★★" if diff < 10 else "★★" if diff < 30 else "★" if diff < 50 else ""
            if match:
                best_pairs.append((name1, name2, total_letters, combo_width, diff, pct, match))
                print(f"{name1:<15} {name2:<15} {total_letters:>10}          {combo_width:>10.1f}px      {diff:>6.1f}px  {pct:>5.1f}%  {match}")

# Also test first + middle name combinations
print(f"\n[TEST 3] Common first + middle combinations:")

DOUBLE_NAMES = [
    "Sarah Kellen",
    "Jean-Luc",
    "Mary Anne",
    "Mary Kay",
    "Jo Ann",
    "Mary Beth",
    "Maria Elena",
    "Anne Marie",
    "Mary Jane",
    "Mary Louise",
    "Mary Margaret",
]

print(f"{'Name':<25} {'Letters':<10} {'Width':<12} {'Diff':<10} {'Error':<10} {'Match'}")
print("-"*90)

for name in DOUBLE_NAMES:
    width = font.getlength(name)
    letters = len(name.replace(" ", ""))
    diff = abs(width - TARGET_W)
    pct = diff / width * 100

    match = "★★★" if diff < 10 else "★★" if diff < 30 else "★" if diff < 50 else ""
    if match or pct < 20:
        print(f"{name:<25} {letters:>6}      {width:>8.1f}px  {diff:>6.1f}px  {pct:>5.1f}%    {match}")

# Best pairs summary
if best_pairs:
    print(f"\n[SUMMARY] Best matching pairs:")
    best_pairs.sort(key=lambda x: x[4])  # Sort by absolute difference
    for name1, name2, letters, width, diff, pct, match in best_pairs[:5]:
        print(f"  {name1} + {name2}: {width:.1f}px (diff: {diff:.1f}px, {pct:.1f}%)")

print(f"\n{'='*100}")
