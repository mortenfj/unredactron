#!/usr/bin/env python3
"""
Advanced Pattern Matching - Compare rendered letters to artifact edges.

This script:
1. Renders each suspect name at the correct scale
2. Simulates a redaction over it
3. Extracts edge patterns from the "artifacts"
4. Compares to actual document artifacts
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image, ImageFont, ImageDraw
import os

FILE_PATH = "files/EFTA00037366.pdf"
FONT_PATH = "fonts/fonts/times.ttf"

# Calibration from earlier analysis
# At 600 DPI, we need to adjust the scale factor
# Original calibration was at ~170 DPI (default pdf2image)
# 600 DPI is 600/170 = 3.53x larger
DPI_RATIO = 600 / 170
SCALE_FACTOR = 2.8998 * DPI_RATIO  # Adjusted for 600 DPI
FONT_SIZE = 12

SUSPECT_NAMES = [
    "Bill Clinton",
    "Jeffrey Epstein",
    "Ghislaine Maxwell",
    "Sarah Kellen",
    "Lesley Groff",
    "Nadia Marcinkova"
]

print("="*100)
print("PATTERN MATCHING - Comparing Rendered Names to Artifacts")
print("="*100)

# Load document at high DPI
print(f"\n[STEP 1] Loading document at 600 DPI...")
images = convert_from_path(FILE_PATH, dpi=600)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

print(f"  ✓ Image loaded: {img.shape[1]}x{img.shape[0]}px")

# Find redactions
print(f"\n[STEP 2] Locating redaction boxes...")
_, black_mask = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

redactions = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if w > 30 and h > 10 and w/h > 1.5:
        redactions.append((x, y, w, h))

print(f"  ✓ Found {len(redactions)} redaction boxes")

# For each suspect name, create a template and match
print(f"\n[STEP 3] Pattern matching suspect names to artifacts...")

font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

results = []

for name in SUSPECT_NAMES:
    print(f"\n--- Analyzing: '{name}' ---")

    # Calculate expected width in document at 600 DPI
    text_width_theoretical = font.getlength(name)
    expected_width = text_width_theoretical * SCALE_FACTOR

    # Find redactions with similar width
    matching_redactions = []
    for x, y, w, h in redactions:
        if abs(w - expected_width) < expected_width * 0.1:  # Within 10%
            matching_redactions.append((x, y, w, h))

    if len(matching_redactions) == 0:
        print(f"  No redactions match expected width of {expected_width:.0f}px")
        continue

    print(f"  Found {len(matching_redactions)} redactions with matching width")

    # Create a template of this name at 600 DPI
    template_height = 200
    template_width = int(expected_width + 100)
    template = Image.new('L', (template_width, template_height), 255)
    draw = ImageDraw.Draw(template)

    # Scale font for 600 DPI (12pt at 72 DPI * 600/72 = 100)
    scaled_font_size = int(FONT_SIZE * 600 / 72)
    scaled_font = ImageFont.truetype(FONT_PATH, scaled_font_size)

    # Draw text centered
    bbox = draw.textbbox((0, 0), name, font=scaled_font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    draw.text((50, (template_height - text_h)//2), name, font=scaled_font, fill=0)

    # Convert to numpy
    template_np = np.array(template)

    # Extract edges from template
    template_edges = cv2.Canny(template_np, 50, 150)

    # Count edge pixels
    template_edge_pixels = np.sum(template_edges > 0)

    print(f"  Template created: {template_width}x{template_height}px")
    print(f"  Edge pixels in template: {template_edge_pixels}")

    # Compare to each matching redaction
    best_match = None
    best_score = 0

    for x, y, w, h in matching_redactions:
        # Extract artifact region (area around redaction)
        padding = 10
        roi_x = max(0, x - padding)
        roi_y = max(0, y - padding)
        roi_w = min(gray.shape[1] - roi_x, w + padding * 2)
        roi_h = min(gray.shape[0] - roi_y, h + padding * 2)

        artifact_roi = gray[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]

        # Enhance contrast
        artifact_enhanced = cv2.normalize(artifact_roi, None, 0, 255, cv2.NORM_MINMAX)

        # Extract edges
        artifact_edges = cv2.Canny(artifact_enhanced, 30, 100)

        # Count edge pixels in the halo (outside the redaction box)
        box_x = x - roi_x
        box_y = y - roi_y

        # Create mask for halo region
        halo_mask = np.ones_like(artifact_edges, dtype=np.uint8) * 255
        halo_mask[box_y:box_y+h, box_x:box_x+w] = 0

        # Get edges in halo only
        halo_edges = cv2.bitwise_and(artifact_edges, artifact_edges, mask=halo_mask)
        artifact_edge_pixels = np.sum(halo_edges > 0)

        # Calculate similarity score
        if template_edge_pixels > 0 and artifact_edge_pixels > 0:
            # Ratio-based comparison
            edge_ratio = min(template_edge_pixels, artifact_edge_pixels) / max(template_edge_pixels, artifact_edge_pixels)

            # Width match quality
            width_diff = abs(w - expected_width)
            width_quality = max(0, 1 - (width_diff / expected_width))

            # Combined score
            combined_score = (edge_ratio * 0.5) + (width_quality * 0.5)

            if combined_score > best_score:
                best_score = combined_score
                best_match = {
                    'x': x,
                    'y': y,
                    'w': w,
                    'h': h,
                    'template_edges': template_edge_pixels,
                    'artifact_edges': artifact_edge_pixels,
                    'score': combined_score
                }

    if best_match:
        results.append({
            'name': name,
            'match': best_match
        })

        print(f"  Best match at ({best_match['x']}, {best_match['y']}):")
        print(f"    Width: {best_match['w']}px (expected: {expected_width:.0f}px)")
        print(f"    Template edges: {best_match['template_edges']}")
        print(f"    Artifact edges: {best_match['artifact_edges']}")
        print(f"    Match score: {best_match['score']*100:.1f}%")

# Print summary
print(f"\n{'='*100}")
print(f"PATTERN MATCHING RESULTS")
print(f"{'='*100}")

if results:
    print(f"\nFound {len(results)} potential matches:")
    print("-"*100)

    # Sort by score
    results.sort(key=lambda x: x['match']['score'], reverse=True)

    for r in results:
        name = r['name']
        m = r['match']
        confidence = "HIGH" if m['score'] > 0.7 else "MEDIUM" if m['score'] > 0.5 else "LOW"

        print(f"\n{name}:")
        print(f"  Location: ({m['x']}, {m['y']}), size: {m['w']}x{m['h']}px")
        print(f"  Match Score: {m['score']*100:.1f}% [{confidence}]")

        if m['score'] > 0.7:
            print(f"  ★ STRONG MATCH - Edge patterns align well")

else:
    print("  No strong pattern matches found")
    print("  This could mean:")
    print("    - Redactions are clean (no artifacts)")
    print("    - Suspect names are not in the document")
    print("    - Font rendering differs from expected")

print(f"\n{'='*100}")
