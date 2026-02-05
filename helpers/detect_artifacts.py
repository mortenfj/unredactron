#!/usr/bin/env python3
"""
Artifact Detection - Find residual pixel traces around redaction boxes.

This script:
1. Converts PDF to high-DPI image (600 DPI)
2. Finds redaction boxes
3. Enhances and analyzes the "halo" region around each box
4. Attempts to detect letter shapes/traces
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image, ImageFont, ImageDraw
import os

FILE_PATH = "files/EFTA00037366.pdf"
FONT_PATH = "fonts/fonts/times.ttf"
OUTPUT_DIR = "artifacts"

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("="*100)
print("ARTIFACT DETECTION - Analyzing Redaction Edges for Text Traces")
print("="*100)

# STEP 1: Convert to high-DPI image
print(f"\n[STEP 1] Converting PDF to 600 DPI image...")
print(f"  This captures sub-pixel details and anti-aliasing traces")

images = convert_from_path(FILE_PATH, dpi=600)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

print(f"  ✓ Image size: {img.shape[1]}x{img.shape[0]}px at 600 DPI")

# STEP 2: Find redaction boxes
print(f"\n[STEP 2] Locating redaction boxes...")

# Threshold to find black areas
_, black_mask = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY_INV)

# Find contours
contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

redactions = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    # Filter for redaction-like rectangles
    if w > 30 and h > 10 and w/h > 1.5:
        redactions.append((x, y, w, h))

redactions.sort(key=lambda b: b[1])  # Sort by Y position
print(f"  ✓ Found {len(redactions)} redaction boxes")

# STEP 3: Analyze artifacts around each box
print(f"\n[STEP 3] Analyzing artifacts around redaction boxes...")

artifact_results = []

for i, (x, y, w, h) in enumerate(redactions):
    # Extract the "halo" region - area slightly larger than the box
    padding = 8  # pixels to examine around the box
    roi_x = max(0, x - padding)
    roi_y = max(0, y - padding)
    roi_w = min(gray.shape[1] - roi_x, w + padding * 2)
    roi_h = min(gray.shape[0] - roi_y, h + padding * 2)

    roi = gray[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]

    # Create mask for the redaction box itself
    box_mask = np.zeros_like(roi)
    box_x = x - roi_x
    box_y = y - roi_y
    box_mask[box_y:box_y+h, box_x:box_x+w] = 255

    # Invert: we want the HALO (area outside the box but inside ROI)
    halo_mask = cv2.bitwise_not(box_mask)

    # Extract just the halo region
    halo = cv2.bitwise_and(roi, roi, mask=halo_mask)

    # ANALYSIS 1: Check for non-black pixels in the halo (potential artifacts)
    halo_pixels = halo[halo_mask > 0]
    if len(halo_pixels) > 0:
        avg_brightness = np.mean(halo_pixels)
        min_brightness = np.min(halo_pixels)
        max_brightness = np.max(halo_pixels)
        std_brightness = np.std(halo_pixels)

        # Count suspicious pixels (not pure white, not pure black)
        suspicious = np.sum((halo_pixels > 20) & (halo_pixels < 235))
        suspicious_ratio = suspicious / len(halo_pixels) * 100
    else:
        avg_brightness = 255
        suspicious = 0
        suspicious_ratio = 0

    # ANALYSIS 2: Edge enhancement to find anti-aliasing
    # Use Canny edge detection on the halo
    edges = cv2.Canny(halo, 30, 100)
    edge_count = np.sum(edges > 0)

    # ANALYSIS 3: Check for descenders/ascenders (protrusions)
    # Look at pixels immediately above and below the box
    top_strip = roi[box_y-2:box_y, box_x:box_x+w] if box_y >= 2 else np.array([])
    bottom_strip = roi[box_y+h:box_y+h+2, box_x:box_x+w] if box_y+h+2 <= roi_h else np.array([])

    top_protrusions = np.sum(top_strip < 50) if len(top_strip) > 0 else 0
    bottom_protrusions = np.sum(bottom_strip < 50) if len(bottom_strip) > 0 else 0

    # Store results
    result = {
        'index': i,
        'x': x,
        'y': y,
        'w': w,
        'h': h,
        'avg_brightness': avg_brightness,
        'suspicious_pixels': suspicious,
        'suspicious_ratio': suspicious_ratio,
        'edge_count': edge_count,
        'top_protrusions': top_protrusions,
        'bottom_protrusions': bottom_protrusions,
        'has_artifacts': suspicious_ratio > 1.0 or edge_count > 50 or top_protrusions > 5 or bottom_protrusions > 5
    }

    artifact_results.append(result)

    # Save enhanced halo image for inspection
    if result['has_artifacts']:
        # Enhance contrast to make artifacts visible
        enhanced = cv2.normalize(halo, None, 0, 255, cv2.NORM_MINMAX)
        enhanced_color = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

        # Draw a box around where the redaction is
        cv2.rectangle(enhanced_color, (box_x, box_y), (box_x+w, box_y+h), (0, 0, 255), 1)

        # Save
        output_path = f"{OUTPUT_DIR}/artifact_{i:03d}_x{x}_y{y}.png"
        cv2.imwrite(output_path, enhanced_color)

# Print summary
print(f"\n{'='*100}")
print(f"ARTIFACT ANALYSIS SUMMARY")
print(f"{'='*100}")

has_artifacts_count = sum(1 for r in artifact_results if r['has_artifacts'])
print(f"\nRedaction boxes with potential artifacts: {has_artifacts_count}/{len(artifact_results)}")

if has_artifacts_count > 0:
    print(f"\nBoxes with significant artifact signals:")
    print("-"*100)

    for r in artifact_results:
        if r['has_artifacts']:
            signals = []
            if r['suspicious_ratio'] > 1.0:
                signals.append(f"suspicious pixels: {r['suspicious_ratio']:.1f}%")
            if r['edge_count'] > 50:
                signals.append(f"edges: {r['edge_count']}")
            if r['top_protrusions'] > 5:
                signals.append(f"top protrusions: {r['top_protrusions']}")
            if r['bottom_protrusions'] > 5:
                signals.append(f"bottom protrusions: {r['bottom_protrusions']}")

            print(f"  Box #{r['index']+1} at ({r['x']}, {r['y']}), size {r['w']}x{r['h']}")
            print(f"    → {', '.join(signals)}")
            print(f"    → Enhanced image saved: {OUTPUT_DIR}/artifact_{r['index']:03d}_x{r['x']}_y{r['y']}.png")

# STEP 4: Template matching for suspect names
print(f"\n{'='*100}")
print(f"STEP 4: Template Matching - Comparing Suspect Names to Artifacts")
print(f"{'='*100}")

# Suspect names to test
SUSPECT_NAMES = [
    "Sarah Kellen", "Ghislaine Maxwell", "Nadia Marcinkova",
    "Lesley Groff", "Jeffrey Epstein", "Bill Clinton"
]

# Font for rendering templates
font = ImageFont.truetype(FONT_PATH, 12)

print(f"\nCreating templates and matching against artifacts...")
print(f"(This simulates what each name would look like redacted)")

for name in SUSPECT_NAMES:
    print(f"\n--- Testing: '{name}' ---")

    # Create a clean template
    template_size = (600, 100)  # Large enough for most names
    template = Image.new('RGB', template_size, 'white')
    draw = ImageDraw.Draw(template)

    # Get text size
    bbox = draw.textbbox((0, 0), name, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Draw text
    draw.text((50, 50 - text_height//2), name, font=font, fill='black')

    # Convert to numpy
    template_np = np.array(template)
    template_gray = cv2.cvtColor(template_np, cv2.COLOR_RGB2GRAY)

    # Find redactions that match this width (within 15px)
    matching_redactions = [r for r in artifact_results if abs(r['w'] - text_width) <= 15]

    for r in matching_redactions:
        x, y, w, h = r['x'], r['y'], r['w'], r['h']

        # Extract the actual artifact region
        padding = 5
        roi_x = max(0, x - padding)
        roi_y = max(0, y - padding)
        roi_w = min(gray.shape[1] - roi_x, w + padding * 2)
        roi_h = min(gray.shape[0] - roi_y, h + padding * 2)

        actual_roi = gray[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]

        # Simple edge comparison
        actual_edges = cv2.Canny(actual_roi, 30, 100)
        template_edges = cv2.Canny(template_gray, 30, 100)

        # Count edge pixels in similar positions
        actual_edge_count = np.sum(actual_edges > 0)
        template_edge_count = np.sum(template_edges > 0)

        if actual_edge_count > 0:
            edge_similarity = min(actual_edge_count, template_edge_count) / max(actual_edge_count, template_edge_count) * 100
        else:
            edge_similarity = 0

        # Calculate width match quality
        width_diff = abs(w - text_width)
        width_quality = max(0, 100 - (width_diff / text_width * 100))

        # Combined score
        combined_score = (edge_similarity * 0.3) + (width_quality * 0.7)

        if combined_score > 80:
            print(f"  ✓ Redaction at ({x},{y}), {w}px wide")
            print(f"    Width match: {width_quality:.1f}% | Edge similarity: {edge_similarity:.1f}%")
            print(f"    Combined score: {combined_score:.1f}%")

print(f"\n{'='*100}")
print(f"ANALYSIS COMPLETE")
print(f"{'='*100}")
print(f"\nEnhanced artifact images saved to: {OUTPUT_DIR}/")
print(f"You can manually inspect these images for letter shapes.")
