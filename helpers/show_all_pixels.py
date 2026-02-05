#!/usr/bin/env python3
"""
Show ALL pixel values at the redaction edge - no filtering.
This will reveal the exact anti-aliasing pattern.
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
import os

FILE_PATH = "files/EFTA00037366.pdf"
OUTPUT_DIR = "pixel_edges"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("="*100)
print("COMPLETE PIXEL ANALYSIS - Showing ALL pixel values at edges")
print("="*100)

# Load at 1200 DPI
images = convert_from_path(FILE_PATH, dpi=1200)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

# Find the 525px redaction
_, black_mask = cv2.threshold(gray, 5, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if 520 < w < 530:
        print(f"\n{'='*100}")
        print(f"525px REDACTION at ({x}, {y}) - Analyzing ALL edge pixels")
        print(f"{'='*100}")

        # Extract edge regions
        border = 20
        left_region = gray[y:y+h, max(0, x-border):x]
        right_region = gray[y:y+h, x:x+min(gray.shape[1]-x, border)]

        print(f"\nLEFT EDGE - Pixel value distribution (first 5 columns):")
        for col in range(min(5, left_region.shape[1])):
            col_data = left_region[:, col]
            print(f"  Column {col}px from edge:")
            print(f"    Min: {np.min(col_data)}, Max: {np.max(col_data)}, Mean: {np.mean(col_data):.1f}")

            # Show sample values
            sample_rows = [0, 50, 100, 150, 211]
            print(f"    Sample values: ", end="")
            for row in sample_rows:
                if row < len(col_data):
                    print(f"{col_data[row]:3d} ", end="")
            print()

            # Count non-white pixels
            non_white = np.sum(col_data < 250)
            if non_white > 0:
                print(f"    → {non_white} pixels are NOT white (<250)")

        print(f"\nRIGHT EDGE - Pixel value distribution (first 5 columns):")
        for col in range(min(5, right_region.shape[1])):
            col_data = right_region[:, col]
            print(f"  Column {col}px from edge:")
            print(f"    Min: {np.min(col_data)}, Max: {np.max(col_data)}, Mean: {np.mean(col_data):.1f}")

            sample_rows = [0, 50, 100, 150, 211]
            print(f"    Sample values: ", end="")
            for row in sample_rows:
                if row < len(col_data):
                    print(f"{col_data[row]:3d} ", end="")
            print()

            non_white = np.sum(col_data < 250)
            if non_white > 0:
                print(f"    → {non_white} pixels are NOT white (<250)")

        # Create visualization showing pixel intensity
        combined = np.hstack([left_region[:, :5], right_region[:, :5]])
        combined_norm = cv2.normalize(combined, None, 0, 255, cv2.NORM_MINMAX)

        # Color map: dark = red, light = blue
        vis_color = cv2.applyColorMap(combined_norm, cv2.COLORMAP_JET)

        # Scale up
        vis_scaled = cv2.resize(vis_color, None, fx=4, fy=1, interpolation=cv2.INTER_NEAREST)

        cv2.imwrite(f"{OUTPUT_DIR}/kellen_pixels_intensity.png", vis_scaled)
        print(f"\nPixel intensity visualization saved: {OUTPUT_DIR}/kellen_pixels_intensity.png")
        print(f"(Red/Warm = dark pixels, Blue/Cool = light pixels)")

        break

print(f"\n{'='*100}")
