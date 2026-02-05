#!/usr/bin/env python3
"""
Protrusion Detection - Look for specific letter parts extending beyond redaction.

This looks for the "tips" and "protrusions" of letters that poke out from
under the redaction box, like the vertical line of 'K' or the curve of 'n'.
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image, ImageFont, ImageDraw
import os

FILE_PATH = "files/EFTA00037366.pdf"
FONT_PATH = "fonts/fonts/times.ttf"
OUTPUT_DIR = "protrusion_analysis"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("="*100)
print("PROTRUSION DETECTION - Finding Letter Parts Extending Beyond Redactions")
print("="*100)

# Load at very high DPI to catch small protrusions
print(f"\n[STEP 1] Loading document at 1200 DPI...")
images = convert_from_path(FILE_PATH, dpi=1200)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

print(f"  ✓ Image loaded: {img.shape[1]}x{img.shape[0]}px")

# Find redactions
print(f"\n[STEP 2] Locating redaction boxes...")
_, black_mask = cv2.threshold(gray, 5, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

redactions = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if 300 < w < 1500 and h > 50:  # Name-sized redactions
        redactions.append((x, y, w, h))

print(f"  ✓ Found {len(redactions)} target redactions")

# Font for template matching
scaled_font_size = int(12 * 1200 / 72)
font = ImageFont.truetype(FONT_PATH, scaled_font_size)

print(f"\n[STEP 3] Analyzing redaction boundaries for protrusions...")

# Analyze left and right edges specifically
for i, (x, y, w, h) in enumerate(redactions[:8]):  # First 8
    print(f"\n{'='*100}")
    print(f"Redaction #{i+1} at ({x}, {y}), size: {w}x{h}px")
    print(f"{'='*100}")

    # Extract the immediate boundary regions (just outside the box)
    boundary_width = 30  # How many pixels outside to look

    # LEFT EDGE: Look for protrusions to the left of the redaction
    left_start = max(0, x - boundary_width)
    left_end = x
    left_region = gray[y:y+h, left_start:left_end]

    # RIGHT EDGE: Look for protrusions to the right
    right_start = x + w
    right_end = min(gray.shape[1], x + w + boundary_width)
    right_region = gray[y:y+h, right_start:right_end]

    print(f"\nLeft edge analysis ({left_region.shape[1]}px wide strip):")

    # Look for dark pixels in the left region (protrusions from letters under the box)
    # These would be pixels that are NOT white but also not pure black
    left_dark = left_region < 150
    left_columns = np.sum(left_dark, axis=0)  # Count dark pixels per column

    # Find columns with significant dark pixels (potential protrusions)
    protrusion_cols = np.where(left_columns > 5)[0]

    if len(protrusion_cols) > 0:
        print(f"  Found {len(protrusion_cols)} columns with potential protrusions")

        # Analyze the vertical distribution of dark pixels
        for col_idx in protrusion_cols:
            col_pixels = left_dark[:, col_idx]
            dark_rows = np.where(col_pixels)[0]

            if len(dark_rows) > 3:  # Need at least a few pixels
                # Check the SHAPE of the protrusion
                row_span = dark_rows[-1] - dark_rows[0]
                top_protrusion = dark_rows[0] < h * 0.3  # Is it near the top?
                bottom_protrusion = dark_rows[-1] > h * 0.7  # Near the bottom?
                middle_protrusion = not (top_protrusion or bottom_protrusion)  # In the middle

                print(f"    Column at {col_idx}px from edge: {len(dark_rows)} dark pixels")
                print(f"      Position: Top={top_protrusion}, Middle={middle_protrusion}, Bottom={bottom_protrusion}")
                print(f"      Span: {row_span}px vertically")

                # Determine likely letter based on position
                if top_protrusion and row_span > h * 0.5:
                    print(f"      → Likely: tall letter (b, d, f, h, k, l, t)")
                elif bottom_protrusion:
                    print(f"      → Likely: descender (g, j, p, q, y)")
                elif middle_protrusion:
                    print(f"      → Likely: middle letter (a, c, e, m, n, o, r, s, u, v, w, x)")

                # Extract and visualize this protrusion
                if len(dark_rows) > 5:
                    protrusion_img = left_region[:, col_idx:col_idx+1]
                    # Save for inspection
                    cv2.imwrite(f"{OUTPUT_DIR}/r{i+1}_left_col{col_idx}.png", protrusion_img)

    else:
        print(f"  No significant protrusions on left edge")

    print(f"\nRight edge analysis ({right_region.shape[1]}px wide strip):")

    # Same analysis for right edge
    right_dark = right_region < 150
    right_columns = np.sum(right_dark, axis=0)
    protrusion_cols = np.where(right_columns > 5)[0]

    if len(protrusion_cols) > 0:
        print(f"  Found {len(protrusion_cols)} columns with potential protrusions")

        for col_idx in protrusion_cols:
            col_pixels = right_dark[:, col_idx]
            dark_rows = np.where(col_pixels)[0]

            if len(dark_rows) > 3:
                row_span = dark_rows[-1] - dark_rows[0]
                top_protrusion = dark_rows[0] < h * 0.3
                bottom_protrusion = dark_rows[-1] > h * 0.7
                middle_protrusion = not (top_protrusion or bottom_protrusion)

                print(f"    Column at {col_idx}px from edge: {len(dark_rows)} dark pixels")
                print(f"      Position: Top={top_protrusion}, Middle={middle_protrusion}, Bottom={bottom_protrusion}")
                print(f"      Span: {row_span}px vertically")

                if top_protrusion and row_span > h * 0.5:
                    print(f"      → Likely: tall letter (b, d, f, h, k, l, t)")
                elif bottom_protrusion:
                    print(f"      → Likely: descender (g, j, p, q, y)")
                elif middle_protrusion:
                    print(f"      → Likely: middle letter (a, c, e, m, n, o, r, s, u, v, w, x)")

                if len(dark_rows) > 5:
                    protrusion_img = right_region[:, col_idx:col_idx+1]
                    cv2.imwrite(f"{OUTPUT_DIR}/r{i+1}_right_col{col_idx}.png", protrusion_img)

    else:
        print(f"  No significant protrusions on right edge")

    # Create a visualization of the edges
    vis_edges = np.zeros((h, boundary_width * 2), dtype=np.uint8)

    # Copy left region
    vis_edges[:, :boundary_width] = left_region

    # Copy right region
    vis_edges[:, boundary_width:] = right_region

    # Enhance contrast
    vis_edges = cv2.normalize(vis_edges, None, 0, 255, cv2.NORM_MINMAX)

    # Add color overlay for dark pixels
    vis_edges_color = cv2.cvtColor(vis_edges, cv2.COLOR_GRAY2BGR)

    # Highlight protrusions in red
    left_protrusions = left_region < 150
    right_protrusions = right_region < 150

    vis_edges_color[:, :boundary_width][left_protrusions] = [0, 0, 255]
    vis_edges_color[:, boundary_width:][right_protrusions] = [0, 0, 255]

    # Add labels
    cv2.putText(vis_edges_color, "LEFT EDGE", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(vis_edges_color, "RIGHT EDGE", (boundary_width + 10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imwrite(f"{OUTPUT_DIR}/r{i+1}_edges.png", vis_edges_color)
    print(f"\n  Edge visualization saved: {OUTPUT_DIR}/r{i+1}_edges.png")

# Summary
print(f"\n{'='*100}")
print(f"ANALYSIS COMPLETE")
print(f"{'='*100}")
print(f"\nEdge images and protrusion samples saved to: {OUTPUT_DIR}/")
print(f"\nLook at the images to identify specific letter parts:")
print(f"  - Vertical lines suggest: b, d, f, h, i, j, k, l, t")
print(f"  - Curves suggest: a, c, e, m, n, o, r, s, u, v, w, x")
print(f"  - Descenders suggest: g, j, p, q, y")
