#!/usr/bin/env python3
"""
Visual artifact analysis - Show enhanced artifacts with letter detection.
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
import os

ARTIFACT_DIR = "artifacts"

print("="*100)
print("VISUAL ARTIFACT ANALYSIS")
print("="*100)

# List artifact files
artifact_files = sorted([f for f in os.listdir(ARTIFACT_DIR) if f.endswith('.png')])

print(f"\nFound {len(artifact_files)} artifact images")
print(f"\nAnalyzing representative samples...")

# Analyze a few interesting ones
samples = artifact_files[:3]  # First 3

for i, artifact_file in enumerate(samples):
    print(f"\n{'='*100}")
    print(f"Sample {i+1}: {artifact_file}")
    print("="*100)

    # Load the artifact image
    img = cv2.imread(os.path.join(ARTIFACT_DIR, artifact_file))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    print(f"Image size: {img.shape[1]}x{img.shape[0]}px")

    # Analyze the halo region (area outside the redaction box)
    # The redaction box is marked with red in the enhanced image

    # Find the red box
    lower_red = np.array([0, 0, 200])
    upper_red = np.array([50, 50, 255])
    red_mask = cv2.inRange(img, lower_red, upper_red)

    # Get coordinates of red box
    red_coords = np.column_stack(np.where(red_mask > 0))
    if len(red_coords) > 0:
        top = red_coords[:, 0].min()
        bottom = red_coords[:, 0].max()
        left = red_coords[:, 1].min()
        right = red_coords[:, 1].max()

        box_width = right - left
        box_height = bottom - top

        print(f"Redaction box: {box_width}x{box_height}px")

        # Extract the halo (area around the box)
        padding = 5
        halo_top = max(0, top - padding)
        halo_bottom = min(gray.shape[0], bottom + padding)
        halo_left = max(0, left - padding)
        halo_right = min(gray.shape[1], right + padding)

        # Get the halo region (everything outside the red box)
        halo_mask = np.ones_like(gray, dtype=np.uint8) * 255
        halo_mask[top:bottom, left:right] = 0

        halo_pixels = gray[halo_mask > 0]

        if len(halo_pixels) > 0:
            # Analyze halo pixel distribution
            print(f"\nHalo Analysis:")
            print(f"  Total halo pixels: {len(halo_pixels)}")
            print(f"  Brightness range: {halo_pixels.min():.0f} - {halo_pixels.max():.0f}")
            print(f"  Average brightness: {halo_pixels.mean():.1f}")
            print(f"  Std deviation: {halo_pixels.std():.1f}")

            # Count pixels by brightness range
            very_dark = np.sum(halo_pixels < 50)
            dark = np.sum((halo_pixels >= 50) & (halo_pixels < 100))
            mid = np.sum((halo_pixels >= 100) & (halo_pixels < 200))
            light = np.sum(halo_pixels >= 200)

            print(f"\nPixel Distribution:")
            print(f"  Very dark (<50):    {very_dark:5d} ({very_dark/len(halo_pixels)*100:5.1f}%)")
            print(f"  Dark (50-100):     {dark:5d} ({dark/len(halo_pixels)*100:5.1f}%)")
            print(f"  Mid (100-200):     {mid:5d} ({mid/len(halo_pixels)*100:5.1f}%)")
            print(f"  Light (>200):      {light:5d} ({light/len(halo_pixels)*100:5.1f}%)")

            # Check for letter-like patterns
            # Letters would create clusters of dark pixels near the edges
            if dark + very_dark > 0:
                print(f"\nArtifact Detection:")
                print(f"  Potential letter traces found: {dark + very_dark} non-white pixels")

                # Check if dark pixels are near edges (expected for anti-aliasing)
                edge_pixels = 0
                if top > padding:
                    top_strip = halo_pixels[:halo_right-halo_left]
                    edge_pixels += np.sum(top_strip < 100)
                if bottom + padding < gray.shape[0]:
                    bottom_start = (bottom - top + padding) * (halo_right - halo_left)
                    bottom_strip = halo_pixels[bottom_start:]
                    edge_pixels += np.sum(bottom_strip < 100)

                if edge_pixels > 0:
                    print(f"  Edge artifacts (anti-aliasing): {edge_pixels} pixels")

    print(f"\nView the artifact image manually:")
    print(f"  File: {ARTIFACT_DIR}/{artifact_file}")

# Summary
print(f"\n{'='*100}")
print(f"SUMMARY")
print(f"{'='*100}")
print(f"\nAll {len(artifact_files)} artifact images have been saved to '{ARTIFACT_DIR}/'")
print(f"\nTo inspect manually:")
print(f"  1. Open an image file in an image viewer")
print(f"  2. Look for dark pixels/shapes near the red box border")
print(f"  3. These may represent traces of the original text")
print(f"\nThe red box in each image marks the redaction boundary.")
print(f"The enhanced contrast makes faint artifacts more visible.")
