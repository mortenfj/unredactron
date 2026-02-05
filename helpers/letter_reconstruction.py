#!/usr/bin/env python3
"""
Letter-by-Letter Reconstruction - Analyze artifact shapes to identify individual letters.

This approach:
1. Analyzes the artifact pattern along the redaction boundary
2. Identifies distinctive features (serifs, curves, vertical strokes)
3. Matches patterns to letter templates
4. Reconstructs text letter by letter

IMPORTANT: All text labels are placed in headers/footers, never over content.
This ensures pixel-perfect forensic artifact integrity.
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image, ImageFont, ImageDraw
import os
import sys
sys.path.append(os.path.dirname(__file__))
from label_utils import add_safe_header, add_multi_line_footer

FILE_PATH = "files/EFTA00037366.pdf"
FONT_PATH = "fonts/fonts/times.ttf"
OUTPUT_DIR = "letter_analysis"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("="*100)
print("LETTER-BY-LETTER RECONSTRUCTION - Artifact Pattern Analysis")
print("="*100)

# Load document
print(f"\n[STEP 1] Loading document at 600 DPI...")
images = convert_from_path(FILE_PATH, dpi=600)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

# Find redactions
print(f"\n[STEP 2] Locating redactions...")
_, black_mask = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

redactions = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if 150 < w < 800 and h > 10:  # Focus on name-sized redactions
        redactions.append((x, y, w, h))

print(f"  ✓ Found {len(redactions)} target redactions")

# Font calibration
SCALE_FACTOR = 10.2346  # From 600 DPI calibration
scaled_font_size = int(12 * 600 / 72)
font = ImageFont.truetype(FONT_PATH, scaled_font_size)

# Letter templates with their distinctive edge patterns
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

# Get letter widths and edge signatures
print(f"\n[STEP 3] Building letter signature database...")

letter_signatures = {}

for letter in LETTERS:
    # Render letter
    template_size = (200, 200)
    template = Image.new('L', template_size, 255)
    draw = ImageDraw.Draw(template)
    draw.text((50, 50), letter, font=font, fill=0)

    # Convert to numpy
    letter_np = np.array(template)

    # Extract edges
    edges = cv2.Canny(letter_np, 50, 150)

    # Count edge pixels in different regions
    h, w = edges.shape

    # Top half (for ascenders)
    top_half = edges[:h//2, :]
    top_edges = np.sum(top_half > 0)

    # Bottom half (for descenders)
    bottom_half = edges[h//2:, :]
    bottom_edges = np.sum(bottom_half > 0)

    # Left side
    left_quarter = edges[:, :w//4]
    left_edges = np.sum(left_quarter > 0)

    # Right side
    right_quarter = edges[:, 3*w//4:]
    right_edges = np.sum(right_quarter > 0)

    # Total edges
    total_edges = np.sum(edges > 0)

    letter_signatures[letter] = {
        'width': font.getlength(letter) * SCALE_FACTOR,
        'top_edges': top_edges,
        'bottom_edges': bottom_edges,
        'left_edges': left_edges,
        'right_edges': right_edges,
        'total_edges': total_edges,
        'ascender': top_edges > bottom_edges * 1.5,
        'descender': bottom_edges > top_edges * 1.5,
    }

print(f"  ✓ Built signatures for {len(letter_signatures)} letters")

# Analyze each redaction
print(f"\n[STEP 4] Analyzing redaction artifact patterns...")

for i, (x, y, w, h) in enumerate(redactions[:5]):  # Analyze first 5
    print(f"\n{'='*100}")
    print(f"Redaction #{i+1} at ({x}, {y}), size: {w}x{h}px")
    print(f"{'='*100}")

    # Extract artifact region with more padding
    padding = 20
    roi_x = max(0, x - padding)
    roi_y = max(0, y - padding)
    roi_w = min(gray.shape[1] - roi_x, w + padding * 2)
    roi_h = min(gray.shape[0] - roi_y, h + padding * 2)

    roi = gray[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]

    # Enhance
    enhanced = cv2.normalize(roi, None, 0, 255, cv2.NORM_MINMAX)

    # Extract edges
    edges = cv2.Canny(enhanced, 20, 80)

    # The redaction box position within the ROI
    box_x = x - roi_x
    box_y = y - roi_y

    # Analyze the top edge (where ascenders would show)
    top_strip = edges[max(0, box_y - 8):box_y, box_x:box_x + w]

    # Analyze the bottom edge (where descenders would show)
    bottom_strip = edges[box_y + h:min(edges.shape[0], box_y + h + 8), box_x:box_x + w]

    # Save visualization
    vis = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
    cv2.rectangle(vis, (box_x, box_y), (box_x + w, box_y + h), (0, 0, 255), 1)

    # Divide the width into segments to identify individual letter positions
    # Estimate letter count
    avg_letter_width = 55  # At 600 DPI
    num_letters = int(round(w / avg_letter_width))
    num_letters = max(3, min(15, num_letters))

    print(f"\nEstimated letter count: {num_letters}")

    # Divide into letter slots
    slot_width = w / num_letters

    print(f"\nAnalyzing {num_letters} letter positions...")

    # Analyze each letter position
    letter_candidates = []

    for slot in range(num_letters):
        slot_start = int(slot * slot_width)
        slot_end = int((slot + 1) * slot_width)

        # Extract this slot from top and bottom strips
        if slot_start < top_strip.shape[1] and slot_end <= top_strip.shape[1]:
            slot_top = top_strip[:, slot_start:slot_end]
            slot_bottom = bottom_strip[:, slot_start:slot_end] if slot_start < bottom_strip.shape[1] else np.array([])

            # Count edge pixels in this slot
            top_edges_count = np.sum(slot_top > 0)
            bottom_edges_count = np.sum(slot_bottom > 0) if slot_bottom.size > 0 else 0

            # Score each letter against this pattern
            letter_scores = []

            for letter, sig in letter_signatures.items():
                # Compare edge patterns
                top_diff = abs(sig['top_edges'] - top_edges_count)
                bottom_diff = abs(sig['bottom_edges'] - bottom_edges_count)

                # Normalize
                max_edges = max(sig['total_edges'], top_edges_count + bottom_edges_count, 1)
                similarity = 100 * (1 - (top_diff + bottom_diff) / (2 * max_edges))

                letter_scores.append((letter, similarity))

            # Get top matches
            letter_scores.sort(key=lambda x: x[1], reverse=True)
            top_3 = letter_scores[:3]

            total_width = slot_end - slot_start

            # Print analysis
            print(f"\n  Position {slot + 1} ({slot_start}-{slot_end}px, width: {total_width}px):")
            print(f"    Edges - Top: {top_edges_count}, Bottom: {bottom_edges_count}")

            for letter, score in top_3:
                if score > 50:
                    sig = letter_signatures[letter]
                    features = []
                    if sig['ascender']:
                        features.append("ascender")
                    if sig['descender']:
                        features.append("descender")

                    print(f"      '{letter}': {score:.1f}% ({', '.join(features) if features else 'normal'})")
                    letter_candidates.append((slot, letter, score))

    # Try to reconstruct from candidates
    if letter_candidates:
        # Get best letter for each position
        reconstruction = []
        for slot in range(num_letters):
            slot_letters = [(l, s) for pos, l, s in letter_candidates if pos == slot]
            if slot_letters:
                slot_letters.sort(key=lambda x: x[1], reverse=True)
                best = slot_letters[0]
                if best[1] > 60:
                    reconstruction.append(best[0])
                else:
                    reconstruction.append('?')

        if reconstruction:
            print(f"\n  Best reconstruction: {''.join(reconstruction)}")

    # Create slot map visualization (BELOW the image, not overlaying)
    # This shows the letter position analysis without obscuring artifacts
    slot_map_h = 100
    slot_map = np.ones((slot_map_h, roi_w), dtype=np.uint8) * 255

    # Draw slot dividers
    for slot in range(num_letters + 1):
        slot_x = int(slot * slot_width)
        cv2.line(slot_map, (slot_x, 0), (slot_x, slot_map_h), 200, 1)

    # Draw slot numbers and labels
    for slot in range(num_letters):
        slot_start = int(slot * slot_width)
        slot_end = int((slot + 1) * slot_width)
        slot_center = (slot_start + slot_end) // 2

        # Get best letter for this slot
        slot_letters = [(l, s) for pos, l, s in letter_candidates if pos == slot]
        if slot_letters:
            slot_letters.sort(key=lambda x: x[1], reverse=True)
            best_letter, best_score = slot_letters[0]
            if best_score > 60:
                label = f"{best_letter}"
                score_text = f"{best_score:.0f}%"
            else:
                label = "?"
                score_text = "?"
        else:
            label = "?"
            score_text = "N/A"

        # Draw slot number
        cv2.putText(slot_map, f"#{slot+1}", (slot_start + 5, 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,), 1)

        # Draw letter
        cv2.putText(slot_map, label, (slot_center - 10, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,), 2)

        # Draw score
        cv2.putText(slot_map, score_text, (slot_center - 15, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (128,), 1)

    # Stack image and slot map vertically
    vis_with_slotmap = np.vstack([vis, slot_map])

    # Add header with analysis summary
    header_text = f"REDACTION #{i+1} - Estimated {num_letters} letters - Reconstruction: {''.join(reconstruction) if reconstruction else 'N/A'}"
    vis_final = add_safe_header(vis_with_slotmap, header_text, header_height=50)

    # Save analysis image
    cv2.imwrite(f"{OUTPUT_DIR}/redaction_{i+1}_analysis.png", vis_final)
    print(f"\n  Visualization saved: {OUTPUT_DIR}/redaction_{i+1}_analysis.png")

print(f"\n{'='*100}")
print(f"ANALYSIS COMPLETE")
print(f"{'='*100}")
print(f"\nArtifact analysis images saved to: {OUTPUT_DIR}/")
print(f"\nEach image shows:")
print(f"  - Enhanced artifact region")
print(f"  - Redaction box outlined in red")
print(f"  - Edge patterns analyzed letter-by-letter")
