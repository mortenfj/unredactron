#!/usr/bin/env python3
"""
Artifact Detection by Subtraction - Remove white background and black redaction,
leaving only the middle range which contains artifacts.
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
import os

FILE_PATH = "files/EFTA00037366.pdf"
OUTPUT_DIR = "artifacts_only"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("="*100)
print("ARTIFACT DETECTION BY SUBTRACTION")
print("Removing white background and black redaction, leaving ONLY artifacts")
print("="*100)

# Load at 1200 DPI
print(f"\nLoading at 1200 DPI...")
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
        print(f"\nFound 525px redaction at ({x}, {y}), size: {w}x{h}px")
        print(f"{'='*100}")

        # Extract edge regions
        border = 20
        left_region = gray[y:y+h, max(0, x-border):x]
        right_region = gray[y:y+h, x:x+min(gray.shape[1]-x, border)]

        print(f"\nLEFT EDGE (looking for 'K'):")

        # SUBTRACT: Remove white (250-255) and black (0-10)
        # What's left (11-249) are artifacts
        left_artifacts = ((left_region >= 11) & (left_region <= 249)).astype(np.uint8) * 255

        artifact_count = np.sum(left_artifacts > 0)
        total_pixels = left_region.size

        print(f"  Total pixels: {total_pixels}")
        print(f"  Artifact pixels (11-249 range): {artifact_count}")
        print(f"  Artifact percentage: {artifact_count/total_pixels*100:.2f}%")

        if artifact_count > 0:
            # Find which columns have artifacts
            for col_idx in range(left_region.shape[1]):
                col_data = left_artifacts[:, col_idx]
                col_artifacts = np.sum(col_data > 0)

                if col_artifacts > 5:
                    print(f"  Column {col_idx}px from edge: {col_artifacts} artifact pixels")

                    # Analyze vertical position
                    artifact_rows = np.where(col_data > 0)[0]
                    if len(artifact_rows) > 0:
                        top = artifact_rows[0]
                        bottom = artifact_rows[-1]
                        mid_h = left_region.shape[0]

                        print(f"    Vertical: rows {top} to {bottom} (of {mid_h})")

                        if top < mid_h * 0.3:
                            print(f"    → UPPER protrusion (tall letter like K)")
                        elif bottom > mid_h * 0.7:
                            print(f"    → LOWER protrusion (descender)")

        print(f"\nRIGHT EDGE (looking for 'ellen'):")

        right_artifacts = ((right_region >= 11) & (right_region <= 249)).astype(np.uint8) * 255

        artifact_count = np.sum(right_artifacts > 0)
        total_pixels = right_region.size

        print(f"  Total pixels: {total_pixels}")
        print(f"  Artifact pixels (11-249 range): {artifact_count}")
        print(f"  Artifact percentage: {artifact_count/total_pixels*100:.2f}%")

        if artifact_count > 0:
            for col_idx in range(right_region.shape[1]):
                col_data = right_artifacts[:, col_idx]
                col_artifacts = np.sum(col_data > 0)

                if col_artifacts > 5:
                    print(f"  Column {col_idx}px from edge: {col_artifacts} artifact pixels")

                    artifact_rows = np.where(col_data > 0)[0]
                    if len(artifact_rows) > 0:
                        top = artifact_rows[0]
                        bottom = artifact_rows[-1]
                        mid_h = right_region.shape[0]

                        print(f"    Vertical: rows {top} to {bottom} (of {mid_h})")

                        if top < mid_h * 0.3:
                            print(f"    → UPPER protrusion")
                        elif bottom > mid_h * 0.7:
                            print(f"    → LOWER protrusion")
                        else:
                            print(f"    → MIDDLE protrusion (x-height letter like 'n')")

        # Create visualization showing ONLY artifacts
        # Combine left and right
        combined = np.hstack([left_artifacts, right_artifacts])

        # Enhance for visibility
        enhanced = cv2.normalize(combined, None, 0, 255, cv2.NORM_MINMAX)

        # Create color version
        vis_color = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

        # Mark the boundary line
        mid_x = left_region.shape[1]
        cv2.line(vis_color, (mid_x, 0), (mid_x, h), (255, 0, 0), 2)

        # Add labels
        cv2.putText(vis_color, "LEFT ('K')", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(vis_color, "RIGHT ('ellen')", (mid_x + 10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Scale up
        vis_scaled = cv2.resize(vis_color, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)

        cv2.imwrite(f"{OUTPUT_DIR}/kellen_artifacts_only.png", vis_scaled)
        print(f"\n  Saved artifact visualization: {OUTPUT_DIR}/kellen_artifacts_only.png")
        print(f"  (Shows ONLY non-white, non-black pixels - the artifacts!)")

        break

print(f"\n{'='*100}")
