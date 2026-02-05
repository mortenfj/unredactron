#!/usr/bin/env python3
"""
Anti-Aliasing Artifact Detection - Look for faint letter traces beyond redaction boundaries.

Based on the EXAMPLE.png which shows how anti-aliased pixels extend beyond
redaction boxes, revealing letter shapes.
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image, ImageFont, ImageDraw
import os

FILE_PATH = "files/EFTA00037366.pdf"
FONT_PATH = "fonts/fonts/times.ttf"
OUTPUT_DIR = "antialiasing_analysis"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("="*100)
print("ANTI-ALIASING ARTIFACT DETECTION")
print("Looking for faint pixel traces beyond redaction boundaries")
print("="*100)

# Load document at HIGH DPI (critical for detecting anti-aliasing)
print(f"\n[STEP 1] Loading document at 1200 DPI for maximum detail...")
images = convert_from_path(FILE_PATH, dpi=1200)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

print(f"  ✓ Image loaded: {img.shape[1]}x{img.shape[0]}px at 1200 DPI")

# Find redactions
print(f"\n[STEP 2] Locating redaction boxes...")

# Use a more sensitive threshold to find pure black
_, black_mask = cv2.threshold(gray, 5, 255, cv2.THRESH_BINARY_INV)

# Find contours
contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

redactions = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if 100 < w < 1500 and h > 20:  # Reasonable text redactions
        redactions.append((x, y, w, h))

redactions.sort(key=lambda b: b[1])
print(f"  ✓ Found {len(redactions)} redaction boxes")

# Analyze each redaction for anti-aliasing artifacts
print(f"\n[STEP 3] Analyzing anti-aliasing artifacts...")

# Font for rendering (at 1200 DPI)
scaled_font_size = int(12 * 1200 / 72)
font = ImageFont.truetype(FONT_PATH, scaled_font_size)

# Scale factor for 1200 DPI
SCALE_FACTOR = 2.8998 * (1200 / 170)

for i, (x, y, w, h) in enumerate(redactions[:10]):  # First 10
    print(f"\n{'='*100}")
    print(f"Redaction #{i+1} at ({x}, {y}), size: {w}x{h}px")
    print(f"{'='*100}")

    # Extract a larger region around the redaction
    padding = 25  # More padding to catch anti-aliasing
    roi_x = max(0, x - padding)
    roi_y = max(0, y - padding)
    roi_w = min(gray.shape[1] - roi_x, w + padding * 2)
    roi_h = min(gray.shape[0] - roi_y, h + padding * 2)

    roi = gray[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]

    # The redaction box position within ROI
    box_x = x - roi_x
    box_y = y - roi_y
    box_w = w
    box_h = h

    # Create a mask for the redaction box
    box_mask = np.zeros((roi_h, roi_w), dtype=np.uint8)
    box_mask[box_y:box_y+box_h, box_x:box_x+box_w] = 255

    # Invert: we want the HALO (area outside the box)
    halo_mask = cv2.bitwise_not(box_mask)

    # Extract the halo region (where artifacts would be)
    halo = cv2.bitwise_and(roi, roi, mask=halo_mask)

    # Key insight: Anti-aliasing creates pixels in the range ~30-200 (not pure black or white)
    # Look specifically for these GRAY pixels
    gray_pixels = halo[(halo > 20) & (halo < 235)]

    if len(gray_pixels) == 0:
        print("  No gray pixels found - clean redaction")
        continue

    # Count suspicious pixels
    suspicious = np.sum((halo > 30) & (halo < 200))
    suspicious_ratio = suspicious / halo.size * 100

    print(f"\nHalo Analysis:")
    print(f"  Total halo pixels: {halo.size}")
    print(f"  Gray pixels (30-200): {len(gray_pixels)} ({len(gray_pixels)/halo.size*100:.1f}%)")
    print(f"  Suspicious pixels (30-200): {suspicious} ({suspicious_ratio:.2f}%)")

    # Analyze specific regions
    # TOP edge (ascenders)
    top_edge = halo[max(0, box_y-8):box_y, box_x:box_x+box_w]
    top_gray = np.sum((top_edge > 30) & (top_edge < 200))

    # BOTTOM edge (descenders)
    bottom_edge = halo[box_y+box_h:min(roi_h, box_y+box_h+8), box_x:box_x+box_w]
    bottom_gray = np.sum((bottom_edge > 30) & (bottom_edge < 200))

    # LEFT edge
    left_edge = halo[box_y:box_y+box_h, max(0, box_x-8):box_x]
    left_gray = np.sum((left_edge > 30) & (left_edge < 200))

    # RIGHT edge
    right_edge = halo[box_y:box_y+box_h, box_x+box_w:min(roi_w, box_x+box_w+8)]
    right_gray = np.sum((right_edge > 30) & (right_edge < 200))

    print(f"\nEdge Artifacts:")
    print(f"  Top (ascenders):    {top_gray:5d} gray pixels")
    print(f"  Bottom (descenders): {bottom_gray:5d} gray pixels")
    print(f"  Left:               {left_gray:5d} gray pixels")
    print(f"  Right:              {right_gray:5d} gray pixels")

    # Create visualization
    vis = roi.copy()

    # Enhance the gray pixels to make them visible
    # Create a mask for gray pixels
    gray_mask = cv2.inRange(halo, 30, 200)

    # Colorize gray pixels in green for visibility
    vis_color = cv2.cvtColor(vis, cv2.COLOR_GRAY2BGR)
    vis_color[gray_mask > 0] = [0, 255, 0]  # Green for artifacts

    # Draw red box around redaction
    cv2.rectangle(vis_color, (box_x, box_y), (box_x + box_w, box_y + box_h), (0, 0, 255), 2)

    # Save visualization
    cv2.imwrite(f"{OUTPUT_DIR}/redaction_{i+1}_antialiasing.png", vis_color)

    if suspicious_ratio > 0.5:
        print(f"\n  ★ ARTIFACTS DETECTED: {suspicious_ratio:.2f}% gray pixels in halo")
        print(f"    Visualization saved: {OUTPUT_DIR}/redaction_{i+1}_antialiasing.png")

        # Now try to identify letters from these artifacts
        print(f"\n  Attempting letter identification from artifacts...")

        # Divide the width into letter positions
        # At 1200 DPI, letters are ~110px wide
        avg_letter_width = 110
        num_letters = max(3, min(15, int(round(w / avg_letter_width))))

        print(f"    Estimated {num_letters} letters")

        # Analyze each letter position
        for letter_pos in range(num_letters):
            pos_start = int(box_x + (letter_pos * w / num_letters))
            pos_end = int(box_x + ((letter_pos + 1) * w / num_letters))

            # Look at the top edge for this letter position
            if pos_start < box_x + w and pos_end <= roi_w:
                letter_region_top = halo[max(0, box_y-10):box_y, pos_start:pos_end]
                letter_region_bottom = halo[box_y+box_h:min(roi_h, box_y+box_h+10), pos_start:pos_end]

                # Count gray pixels
                top_gray_count = np.sum((letter_region_top > 30) & (letter_region_top < 200))
                bottom_gray_count = np.sum((letter_region_bottom > 30) & (letter_region_bottom < 200))

                # Detect features
                has_ascender = top_gray_count > 50
                has_descender = bottom_gray_count > 50

                # Make a guess based on features
                if has_ascender and not has_descender:
                    likely = "bdfhkl"  # Tall letters
                elif not has_ascender and has_descender:
                    likely = "gjpqy"  # Letters with tails
                elif has_ascender and has_descender:
                    likely = "unclear"  # Rare
                else:
                    # Could be round or middle letters
                    likely = "aceomnrsuvwxz"

                if top_gray_count + bottom_gray_count > 20:
                    print(f"    Position {letter_pos+1}: ascender={has_ascender}, descender={has_descender}")
                    print(f"      → Likely: {likely}")
    else:
        print(f"\n  Clean redaction - no significant anti-aliasing detected")

print(f"\n{'='*100}")
print(f"ANALYSIS COMPLETE")
print(f"{'='*100}")
print(f"\nVisualization images saved to: {OUTPUT_DIR}/")
print(f"\nGreen pixels in the images indicate detected anti-aliasing artifacts.")
print(f"These are the faint traces that may reveal the original text.")
