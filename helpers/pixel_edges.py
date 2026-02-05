#!/usr/bin/env python3
"""
Pixel-level boundary analysis - Show the exact edge pixels
where letter parts protrude from the redaction.
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
import os

FILE_PATH = "files/EFTA00037366.pdf"
OUTPUT_DIR = "pixel_edges"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("="*100)
print("PIXEL-LEVEL BOUNDARY ANALYSIS")
print("Showing exact pixels at the redaction edges")
print("="*100)

# Load at 1200 DPI
images = convert_from_path(FILE_PATH, dpi=1200)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

# Find the 525px redaction (Kellen match)
_, black_mask = cv2.threshold(gray, 5, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Find the 525px redaction
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if 520 < w < 530:  # The Kellen redaction
        print(f"\nFound 525px redaction at ({x}, {y})")
        print(f"{'='*100}")

        # Extract a wider border area to see protrusions
        border = 30  # pixels

        # Left edge region
        left_region = gray[y:y+h, max(0, x-border):x]

        # Right edge region
        right_region = gray[y:y+h, x:x+min(gray.shape[1]-x, border)]

        print(f"\nLEFT EDGE ANALYSIS (looking for 'K'):")
        print(f"Left region size: {left_region.shape[1]}x{left_region.shape[0]}px")

        # Show pixel values at the immediate boundary
        print("\nPixel values at left boundary (first 15 columns):")
        for col in range(min(15, left_region.shape[1])):
            col_data = left_region[:, col]

            # Find dark pixels (<200)
            dark_pixels = np.sum(col_data < 200)
            very_dark = np.sum(col_data < 100)
            darkest = np.min(col_data)

            if dark_pixels > 10:
                print(f"  Column {col}px from edge: {dark_pixels} pixels <200, darkest={darkest}")

                # Find vertical extent
                dark_rows = np.where(col_data < 200)[0]
                if len(dark_rows) > 0:
                    row_span = dark_rows[-1] - dark_rows[0]
                    print(f"    Vertical span: {row_span}px (rows {dark_rows[0]} to {dark_rows[-1]})")

        print(f"\nRIGHT EDGE ANALYSIS (looking for 'n'):")
        print(f"Right region size: {right_region.shape[1]}x{right_region.shape[0]}px")

        print("\nPixel values at right boundary (first 15 columns):")
        for col in range(min(15, right_region.shape[1])):
            col_data = right_region[:, col]

            dark_pixels = np.sum(col_data < 200)
            very_dark = np.sum(col_data < 100)
            darkest = np.min(col_data)

            if dark_pixels > 10:
                print(f"  Column {col}px from edge: {dark_pixels} pixels <200, darkest={darpest}")

                dark_rows = np.where(col_data < 200)[0]
                if len(dark_rows) > 0:
                    row_span = dark_rows[-1] - dark_rows[0]
                    print(f"    Vertical span: {row_span}px (rows {dark_rows[0]} to {dark_rows[-1]})")

        # Create enhanced visualization
        # Combine left and right regions
        combined_width = left_region.shape[1] + right_region.shape[1]
        combined = np.zeros((h, combined_width), dtype=np.uint8)

        combined[:, :left_region.shape[1]] = left_region
        combined[:, left_region.shape[1]:] = right_region

        # Enhance contrast
        enhanced = cv2.normalize(combined, None, 0, 255, cv2.NORM_MINMAX)

        # Create color visualization
        vis = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

        # Highlight very dark pixels (<150) in green
        very_dark_mask = enhanced < 150
        vis[very_dark_mask] = [0, 255, 0]

        # Highlight moderately dark pixels (150-200) in yellow
        moderate_dark_mask = (enhanced >= 150) & (enhanced < 200)
        vis[moderate_dark_mask] = [0, 255, 255]

        # Add dividing line
        mid_x = left_region.shape[1]
        cv2.line(vis, (mid_x, 0), (mid_x, h), (255, 0, 0), 2)

        # Add labels
        cv2.putText(vis, "LEFT EDGE ('K')", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(vis, "RIGHT EDGE ('n')", (mid_x + 10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Scale up
        vis_scaled = cv2.resize(vis, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)

        cv2.imwrite(f"{OUTPUT_DIR}/kellen_525px_edges.png", vis_scaled)
        print(f"\nEnhanced edge visualization saved: {OUTPUT_DIR}/kellen_525px_edges.png")
        print(f"Green pixels = very dark (<150)")
        print(f"Yellow pixels = moderately dark (150-200)")

        break

print(f"\n{'='*100}")
print(f"ANALYSIS COMPLETE")
print(f"{'='*100}")
