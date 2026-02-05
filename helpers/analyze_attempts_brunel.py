#!/usr/bin/env python3
"""
Forensic Analysis: "Attempts were made to [REDACTED] and Brunel"

Target: 962px redaction at (2475, 3462) between "Attempts" (575, 3500) and "Brunel" (3837, 3500)
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import ImageFont, ImageDraw
import pytesseract
import os

FILE_PATH = "files/EFTA00037366.pdf"
FONT_PATH = "fonts/fonts/times.ttf"
OUTPUT_DIR = "brunel_analysis"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("="*100)
print("FORENSIC ANALYSIS: 'Attempts were made to [REDACTED] and Brunel'")
print("="*100)

# Load at 1200 DPI
print(f"\nLoading at 1200 DPI...")
images = convert_from_path(FILE_PATH, dpi=1200)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

# Target redaction (found from previous search)
target_x, target_y, target_w, target_h = 2475, 3462, 962, 213

print(f"\n[STEP 1] Target Redaction at ({target_x}, {target_y}), size: {target_w}x{target_h}px")

# Font setup for width analysis
font_size = int(12 * 1200 / 72)
font = ImageFont.truetype(FONT_PATH, font_size)

# Candidate names (capitalized first letter as user specified)
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

print(f"\n[STEP 2] WIDTH ANALYSIS - {len(CANDIDATES)} candidates")
print(f"{'Name':<20} {'Expected':<12} {'Actual':<10} {'Diff':<10} {'Error':<10} {'Match'}")
print("-"*80)

width_matches = []
for name in CANDIDATES:
    expected = font.getlength(name)
    diff = abs(expected - target_w)
    pct_error = diff / expected * 100

    match = "✓" if diff < expected * 0.15 else "✗"
    if diff < expected * 0.15:
        width_matches.append((name, diff, pct_error))

    print(f"{name:<20} {expected:>10.1f}px  {target_w:>8}px  {diff:>6.1f}px  {pct_error:>5.1f}%   {match}")

# PILLAR 2: SPACING ANALYSIS
print(f"\n[STEP 3] SPACING ANALYSIS")

avg_char_width = 55  # At 1200 DPI
estimated_chars = round(target_w / avg_char_width)
print(f"  Width: {target_w}px ÷ {avg_char_width}px/char ≈ {estimated_chars} characters")

spacing_matches = []
for name, diff, pct in width_matches:
    if len(name) == estimated_chars:
        spacing_matches.append(name)
        print(f"  '{name}' has {len(name)} letters ✓")

# PILLAR 3: ARTIFACT ANALYSIS (subtraction method)
print(f"\n[STEP 4] ARTIFACT ANALYSIS (subtraction method)")

# Extract edges
border = 20
left_region = gray[target_y:target_y+target_h, max(0, target_x-border):target_x]
right_region = gray[target_y:target_y+target_h, target_x:target_x+min(gray.shape[1]-target_x, border)]

# Subtract white (250-255) and black (0-10), keep artifacts (11-249)
left_artifacts = ((left_region >= 11) & (left_region <= 249)).astype(np.uint8) * 255
right_artifacts = ((right_region >= 11) & (right_region <= 249)).astype(np.uint8) * 255

# Exclude corners (top/bottom 10%)
top_cutoff = int(target_h * 0.1)
bottom_cutoff = int(target_h * 0.9)

left_middle = left_artifacts[top_cutoff:bottom_cutoff, :]
right_middle = right_artifacts[top_cutoff:bottom_cutoff, :]

# Analyze left edge (first letter)
left_artifact_count = np.sum(left_middle > 0)
left_has_upper = False
left_has_lower = False

for col_idx in range(left_middle.shape[1]):
    col = left_middle[:, col_idx]
    dark_rows = np.where(col > 0)[0]
    if len(dark_rows) > 10:
        position = dark_rows[0]
        mid_h = bottom_cutoff - top_cutoff
        if position < mid_h * 0.3:
            left_has_upper = True
        elif position > mid_h * 0.7:
            left_has_lower = True

# Analyze right edge (last letter)
right_artifact_count = np.sum(right_middle > 0)
right_has_upper = False
right_has_lower = False

for col_idx in range(right_middle.shape[1]):
    col = right_middle[:, col_idx]
    dark_rows = np.where(col > 0)[0]
    if len(dark_rows) > 10:
        position = dark_rows[0]
        mid_h = bottom_cutoff - top_cutoff
        if position < mid_h * 0.3:
            right_has_upper = True
        elif position > mid_h * 0.7:
            right_has_lower = True

print(f"  LEFT edge (first letter):")
print(f"    Artifact pixels: {left_artifact_count}")
print(f"    Has upper protrusion: {left_has_upper}")
print(f"    Has lower protrusion: {left_has_lower}")

print(f"  RIGHT edge (last letter):")
print(f"    Artifact pixels: {right_artifact_count}")
print(f"    Has upper protrusion: {right_has_upper}")
print(f"    Has lower protrusion: {right_has_lower}")

# COMBINED ANALYSIS
print(f"\n[STEP 5] COMBINED ANALYSIS - Matching candidates to all three pillars:")

for name, diff, pct in width_matches:
    # First letter features
    first_letter = name[0]
    first_has_upper = first_letter in 'BDFHKLT'
    first_has_lower = first_letter in 'GJPQYgjpqy'

    # Last letter features
    last_letter = name[-1]
    last_has_upper = last_letter in 'BDFHKLT'
    last_has_lower = last_letter in 'GJPQYgjpqy'

    # Check artifact match
    artifact_score = 100

    if left_artifact_count > 100:
        if left_has_upper and first_has_upper:
            artifact_score += 25  # Matches expected upper
        elif left_has_lower and first_has_lower:
            artifact_score += 25  # Matches expected lower
        elif not first_has_upper and not first_has_lower:
            artifact_score += 25  # Correctly no protrusion
        else:
            artifact_score -= 50  # Unexpected

    if right_artifact_count > 100:
        if last_has_upper and right_has_upper:
            artifact_score += 25
        elif last_has_lower and right_has_lower:
            artifact_score += 25
        elif not last_has_upper and not last_has_lower:
            artifact_score += 25
        else:
            artifact_score -= 50

    width_score = 100 - pct

    combined = (width_score * 0.5) + (artifact_score * 0.5)

    print(f"\n  {name}:")
    print(f"    First letter '{first_letter}': upper={first_has_upper}, lower={first_has_lower}")
    print(f"    Last letter '{last_letter}': upper={last_has_upper}, lower={last_has_lower}")
    print(f"    Width match: {width_score:.1f}%")
    print(f"    Artifact match: {artifact_score:.1f}%")
    print(f"    COMBINED: {combined:.1f}%")

    if combined > 75:
        print(f"    ★ STRONG MATCH")
    elif combined > 60:
        print(f"    → Moderate match")
    else:
        print(f"    ✗ Weak match")

# Create visualization
vis_x = max(0, target_x - 50)
vis_y = max(0, target_y - 50)
vis_w = min(gray.shape[1] - vis_x, target_w + 100)
vis_h = min(gray.shape[0] - vis_y, target_h + 100)

region = gray[vis_y:vis_y+vis_h, vis_x:vis_x+vis_w].copy()
region_color = cv2.cvtColor(region, cv2.COLOR_GRAY2BGR)

box_x = target_x - vis_x
box_y = target_y - vis_y

cv2.rectangle(region_color, (box_x, box_y), (box_x + target_w, box_y + target_h), (0, 0, 255), 3)

# Add best match
if width_matches:
    best_name = width_matches[0][0]
    cv2.putText(region_color, f"Width: {target_w}px (best: '{best_name}')",
               (10, vis_h - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

cv2.imwrite(f"{OUTPUT_DIR}/attempts_brunel_redaction.png", region_color)
print(f"\n  Visualization saved: {OUTPUT_DIR}/attempts_brunel_redaction.png")

print(f"\n{'='*100}")
