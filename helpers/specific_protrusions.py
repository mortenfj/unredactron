#!/usr/bin/env python3
"""
Specific Protrusion Detection - Look for small letter parts, ignoring corners.
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
import os

FILE_PATH = "files/EFTA00037366.pdf"
OUTPUT_DIR = "specific_protrusions"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("="*100)
print("SPECIFIC PROTRUSION DETECTION - Finding Letter Tips, Ignoring Corners")
print("="*100)

# Load at 1200 DPI
print(f"\n[STEP 1] Loading document at 1200 DPI...")
images = convert_from_path(FILE_PATH, dpi=1200)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

# Find redactions
print(f"\n[STEP 2] Locating redaction boxes...")
_, black_mask = cv2.threshold(gray, 5, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

redactions = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if 300 < w < 1500 and h > 50:
        redactions.append((x, y, w, h))

print(f"  ✓ Found {len(redactions)} target redactions")

print(f"\n[STEP 3] Looking for SMALL protrusions (letter tips), excluding corners...")

for i, (x, y, w, h) in enumerate(redactions[:8]):
    print(f"\n{'='*100}")
    print(f"Redaction #{i+1} at ({x}, {y}), size: {w}x{h}px")
    print(f"{'='*100}")

    # Extract left edge (15px strip)
    left_start = max(0, x - 15)
    left_end = x
    left_region = gray[y:y+h, left_start:left_end]

    # Extract right edge
    right_start = x + w
    right_end = min(gray.shape[1], x + w + 15)
    right_region = gray[y:y+h, right_start:right_end]

    # EXCLUDE CORNERS - only look at middle 80% vertically
    top_cutoff = int(h * 0.1)  # Exclude top 10%
    bottom_cutoff = int(h * 0.9)  # Exclude bottom 10%

    print(f"\nLeft edge (excluding corners, looking at middle {h - 2*top_cutoff}px):")

    # Analyze left edge, excluding corners
    left_middle = left_region[top_cutoff:bottom_cutoff, :]

    # Look for very specific, small protrusions
    # Use adaptive threshold to find pixels that are darker than surrounding area
    for col_idx in range(left_middle.shape[1]):
        col = left_middle[:, col_idx]

        # Find dark pixels (actual letter tips, not anti-aliasing)
        dark_threshold = 100  # Tighter threshold
        dark_mask = col < dark_threshold
        dark_rows = np.where(dark_mask)[0]

        if len(dark_rows) > 0 and len(dark_rows) < 30:  # Small protrusion, not full height
            # Check the vertical SPAN of the protrusion
            span = dark_rows[-1] - dark_rows[0] + 1

            # Check position within the middle section
            position = dark_rows[0] + top_cutoff

            print(f"  Column {col_idx}px from edge: {len(dark_rows)} dark pixels, span={span}px")
            print(f"    Position: {position}px from top of redaction")

            # Identify likely letter part based on span and position
            if span < 10:
                print(f"    → Small tip - likely serif or stroke end")
            elif span < 30:
                if position < h * 0.4:
                    print(f"    → Upper protrusion - likely b, d, f, h, k, l, t")
                elif position > h * 0.6:
                    print(f"    → Lower protrusion - likely descender (g, j, p, q, y)")
                else:
                    print(f"    → Middle protrusion - likely x-height letter")
            else:
                print(f"    → Larger feature - unclear")

    print(f"\nRight edge (excluding corners):")

    # Same for right edge
    right_middle = right_region[top_cutoff:bottom_cutoff, :]

    for col_idx in range(right_middle.shape[1]):
        col = right_middle[:, col_idx]

        dark_mask = col < 100
        dark_rows = np.where(dark_mask)[0]

        if len(dark_rows) > 0 and len(dark_rows) < 30:
            span = dark_rows[-1] - dark_rows[0] + 1
            position = dark_rows[0] + top_cutoff

            print(f"  Column {col_idx}px from edge: {len(dark_rows)} dark pixels, span={span}px")
            print(f"    Position: {position}px from top of redaction")

            if span < 10:
                print(f"    → Small tip - likely serif or stroke end")
            elif span < 30:
                if position < h * 0.4:
                    print(f"    → Upper protrusion - likely b, d, f, h, k, l, t")
                elif position > h * 0.6:
                    print(f"    → Lower protrusion - likely descender (g, j, p, q, y)")
                else:
                    print(f"    → Middle protrusion - likely x-height letter")

    # Create visualization highlighting the middle section only
    vis_height = h
    vis_width = 30  # 15px on each side
    vis = np.zeros((vis_height, vis_width), dtype=np.uint8)

    # Copy left middle section
    vis[top_cutoff:bottom_cutoff, :15] = left_middle

    # Copy right middle section
    vis[top_cutoff:bottom_cutoff, 15:] = right_middle

    # Enhance contrast
    vis = cv2.normalize(vis, None, 0, 255, cv2.NORM_MINMAX)

    # Highlight protrusions in green
    vis_color = cv2.cvtColor(vis, cv2.COLOR_GRAY2BGR)

    # Mark corners as grayed out
    corner_mask = np.zeros((vis_height, vis_width, 3), dtype=np.uint8)
    corner_mask[:top_cutoff, :] = [128, 128, 128]
    corner_mask[bottom_cutoff:, :] = [128, 128, 128]

    vis_color = cv2.addWeighted(vis_color, 1, corner_mask, 0.3, 0)

    # Highlight dark pixels
    dark_pixels = vis < 100
    vis_color[dark_pixels] = [0, 255, 0]  # Green

    cv2.imwrite(f"{OUTPUT_DIR}/r{i+1}_protrusions.png", vis_color)
    print(f"\n  Protrusion visualization saved: {OUTPUT_DIR}/r{i+1}_protrusions.png")

print(f"\n{'='*100}")
print(f"ANALYSIS COMPLETE")
print(f"{'='*100}")
print(f"\nProtrusion visualizations saved to: {OUTPUT_DIR}/")
print(f"Gray areas = excluded corners")
print(f"Green pixels = detected letter protrusions")
