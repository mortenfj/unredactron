#!/usr/bin/env python3
"""
Create annotated visualization showing redactions with protrusion callouts.
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
import os

FILE_PATH = "files/EFTA00037366.pdf"
OUTPUT_DIR = "visualizations"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("="*100)
print("Creating annotated visualizations of redactions with protrusions")
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
    if 300 < w < 800:  # Name-sized redactions
        redactions.append((x, y, w, h))

print(f"Found {len(redactions)} redactions")

# Process each redaction
for i, (x, y, w, h) in enumerate(redactions[:8]):
    print(f"\nRedaction #{i+1} at ({x}, {y}), size: {w}x{h}px")

    # Extract the area around the redaction with context
    context_padding = 100
    vis_x = max(0, x - context_padding)
    vis_y = max(0, y - 50)
    vis_w = min(gray.shape[1] - vis_x, w + context_padding * 2)
    vis_h = min(gray.shape[0] - vis_y, h + 100)

    # Extract region
    region = gray[vis_y:vis_y+vis_h, vis_x:vis_x+vis_w].copy()

    # Convert to color
    region_color = cv2.cvtColor(region, cv2.COLOR_GRAY2BGR)

    # Redaction box position within region
    box_x = x - vis_x
    box_y = y - vis_y

    # Draw red box around the redaction
    cv2.rectangle(region_color, (box_x, box_y), (box_x + w, box_y + h), (0, 0, 255), 3)

    # Look for protrusions
    left_start = max(0, x - 20)
    left_end = x
    left_region = gray[y:y+h, left_start:left_end]

    right_start = x + w
    right_end = min(gray.shape[1], x + w + 20)
    right_region = gray[y:y+h, right_start:right_end]

    # Find protrusions (exclude corners)
    top_cutoff = int(h * 0.1)
    bottom_cutoff = int(h * 0.9)

    left_middle = left_region[top_cutoff:bottom_cutoff, :]
    right_middle = right_region[top_cutoff:bottom_cutoff, :]

    # Detect and mark left protrusions
    left_protrusions = []
    for col_idx in range(left_middle.shape[1]):
        col = left_middle[:, col_idx]
        dark_rows = np.where(col < 100)[0]

        if len(dark_rows) > 0 and len(dark_rows) < 30:
            # Found a protrusion
            protrusion_x = box_x - 20 + col_idx
            protrusion_y_start = box_y + top_cutoff + dark_rows[0]
            protrusion_y_end = box_y + top_cutoff + dark_rows[-1]

            # Determine type
            position = dark_rows[0]
            mid_h = bottom_cutoff - top_cutoff

            if position < mid_h * 0.3:
                p_type = "UPPER"
                color = [255, 0, 0]  # Red for upper
            elif position > mid_h * 0.7:
                p_type = "LOWER"
                color = [0, 0, 255]  # Blue for lower
            else:
                p_type = "MIDDLE"
                color = [0, 255, 0]  # Green for middle

            # Draw arrow pointing to it
            arrow_x = protrusion_x - 30
            arrow_y = protrusion_y_start + (protrusion_y_end - protrusion_y_start) // 2

            cv2.arrowedLine(region_color,
                           (int(arrow_x), int(arrow_y)),
                           (int(protrusion_x), int(arrow_y)),
                           color, 3, tipLength=0.3)

            # Add label
            label_y = arrow_y - 20 if arrow_y > 20 else arrow_y + 30
            cv2.putText(region_color, p_type, (int(arrow_x - 60), int(label_y)),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            left_protrusions.append(p_type)

    # Detect and mark right protrusions
    right_protrusions = []
    for col_idx in range(right_middle.shape[1]):
        col = right_middle[:, col_idx]
        dark_rows = np.where(col < 100)[0]

        if len(dark_rows) > 0 and len(dark_rows) < 30:
            protrusion_x = box_x + w + col_idx
            protrusion_y_start = box_y + top_cutoff + dark_rows[0]
            protrusion_y_end = box_y + top_cutoff + dark_rows[-1]

            position = dark_rows[0]
            mid_h = bottom_cutoff - top_cutoff

            if position < mid_h * 0.3:
                p_type = "UPPER"
                color = [255, 0, 0]
            elif position > mid_h * 0.7:
                p_type = "LOWER"
                color = [0, 0, 255]
            else:
                p_type = "MIDDLE"
                color = [0, 255, 0]

            arrow_x = protrusion_x + 30
            arrow_y = protrusion_y_start + (protrusion_y_end - protrusion_y_start) // 2

            cv2.arrowedLine(region_color,
                           (int(arrow_x), int(arrow_y)),
                           (int(protrusion_x), int(arrow_y)),
                           color, 3, tipLength=0.3)

            label_y = arrow_y - 20 if arrow_y > 20 else arrow_y + 30
            cv2.putText(region_color, p_type, (int(arrow_x + 10), int(label_y)),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            right_protrusions.append(p_type)

    # Add title
    cv2.putText(region_color, f"Redaction #{i+1} ({w}px wide)",
               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Add width info - position it in bottom corner, away from redaction
    info_text = f"Left: {len(left_protrusions)} tips | Right: {len(right_protrusions)} tips"
    text_y = vis_h - 20  # Bottom of image
    cv2.putText(region_color, info_text,
               (10, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

    # Scale up for visibility
    scale = 2
    region_scaled = cv2.resize(region_color, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)

    cv2.imwrite(f"{OUTPUT_DIR}/redaction_{i+1}_annotated.png", region_scaled)

    print(f"  Left protrusions: {left_protrusions}")
    print(f"  Right protrusions: {right_protrusions}")
    print(f"  Saved: {OUTPUT_DIR}/redaction_{i+1}_annotated.png")

print(f"\n{'='*100}")
print(f"Done! Annotated visualizations saved to: {OUTPUT_DIR}/")
print(f"{'='*100}")
print(f"\nEach image shows:")
print(f"  - The redaction box (red outline)")
print(f"  - Arrows pointing to detected protrusions")
print(f"  - UPPER (red) = tall letters (b, d, f, h, k, l, t)")
print(f"  - LOWER (blue) = descenders (g, j, p, q, y)")
print(f"  - MIDDLE (green) = x-height letters")
