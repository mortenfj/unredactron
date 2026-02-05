#!/usr/bin/env python3
"""
Detailed Forensic Analysis - Focus on the strongest pattern match.

This performs deep analysis on the redaction that matched "Jeffrey Epstein"
with 81.2% confidence, examining specific artifact features.

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
OUTPUT_DIR = "detailed_analysis"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# The strong match from earlier analysis
TARGET_REDACTION = (368, 3531, 713, 107)  # x, y, w, h
CANDIDATE_NAME = "Jeffrey Epstein"

print("="*100)
print(f"DETAILED FORENSIC ANALYSIS")
print(f"Target: Redaction at ({TARGET_REDACTION[0]}, {TARGET_REDACTION[1]})")
print(f"Candidate: '{CANDIDATE_NAME}'")
print("="*100)

# Load document
print(f"\n[STEP 1] Loading document at 600 DPI...")
images = convert_from_path(FILE_PATH, dpi=600)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

x, y, w, h = TARGET_REDACTION

# Extract artifact region with large padding
padding = 30
roi_x = max(0, x - padding)
roi_y = max(0, y - padding)
roi_w = min(gray.shape[1] - roi_x, w + padding * 2)
roi_h = min(gray.shape[0] - roi_y, h + padding * 2)

actual_artifact = gray[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]

print(f"  ✓ Artifact region: {roi_w}x{roi_h}px")

# Create template of candidate name
print(f"\n[STEP 2] Creating template for '{CANDIDATE_NAME}'...")

SCALE_FACTOR = 10.2346  # From 600 DPI calibration
scaled_font_size = int(12 * 600 / 72)
font = ImageFont.truetype(FONT_PATH, scaled_font_size)

# Create template with same dimensions
template = Image.new('L', (roi_w, roi_h), 255)
draw = ImageDraw.Draw(template)

# Get text size
bbox = draw.textbbox((0, 0), CANDIDATE_NAME, font=font)
text_w = bbox[2] - bbox[0]
text_h = bbox[3] - bbox[1]

# Position text to match redaction location
text_x = padding
text_y = (roi_h - text_h) // 2

draw.text((text_x, text_y), CANDIDATE_NAME, font=font, fill=0)

template_np = np.array(template)

# Simulate redaction over template
template_with_redaction = template_np.copy()
redaction_x = padding
redaction_y = text_y - 5
redaction_w = text_w
redaction_h = text_h + 10

cv2.rectangle(template_with_redaction,
              (redaction_x, redaction_y),
              (redaction_x + redaction_w, redaction_y + redaction_h),
              0, -1)

# Extract halo from template (artifacts that would remain)
halo_mask = np.ones_like(template_with_redaction, dtype=np.uint8) * 255
halo_mask[redaction_y:redaction_y+redaction_h, redaction_x:redaction_x+redaction_w] = 0

template_halo = cv2.bitwise_and(template_with_redaction, template_with_redaction, mask=halo_mask)

print(f"  ✓ Template created: {roi_w}x{roi_h}px")
print(f"  ✓ Text position: ({text_x}, {text_y}), size: {text_w}x{text_h}px")

# Extract edges from both
print(f"\n[STEP 3] Extracting edge patterns...")

# Enhance actual artifact
actual_enhanced = cv2.normalize(actual_artifact, None, 0, 255, cv2.NORM_MINMAX)

# Extract edges with multiple thresholds
actual_edges_strong = cv2.Canny(actual_enhanced, 50, 150)
actual_edges_weak = cv2.Canny(actual_enhanced, 20, 80)

template_edges_strong = cv2.Canny(template_halo, 50, 150)
template_edges_weak = cv2.Canny(template_halo, 20, 80)

print(f"  ✓ Strong edges (50-150 threshold)")
print(f"  ✓ Weak edges (20-80 threshold)")

# Detailed comparison
print(f"\n[STEP 4] Detailed edge pattern comparison...")

def analyze_edges(edges, name):
    """Analyze edge pattern characteristics."""
    total_edges = np.sum(edges > 0)

    # Divide into regions
    h, w = edges.shape
    top_third = edges[:h//3, :]
    middle_third = edges[h//3:2*h//3, :]
    bottom_third = edges[2*h//3:, :]

    top_count = np.sum(top_third > 0)
    middle_count = np.sum(middle_third > 0)
    bottom_count = np.sum(bottom_third > 0)

    # Left and right edges
    left_quarter = edges[:, :w//4]
    right_quarter = edges[:, 3*w//4:]

    left_count = np.sum(left_quarter > 0)
    right_count = np.sum(right_quarter > 0)

    return {
        'total': total_edges,
        'top': top_count,
        'middle': middle_count,
        'bottom': bottom_count,
        'left': left_count,
        'right': right_count,
    }

print(f"\nEdge Analysis Comparison:")
print("-"*100)

actual_stats = analyze_edges(actual_edges_strong, "Actual")
template_stats = analyze_edges(template_edges_strong, "Template")

print(f"{'Metric':<20} {'Actual':<15} {'Template':<15} {'Match':<15}")
print("-"*100)

for metric in ['total', 'top', 'middle', 'bottom', 'left', 'right']:
    actual_val = actual_stats[metric]
    template_val = template_stats[metric]

    if template_val > 0:
        diff = abs(actual_val - template_val)
        match_pct = max(0, 100 - (diff / template_val * 100))
    else:
        match_pct = 100 if actual_val == 0 else 0

    status = "✓" if match_pct > 80 else "~" if match_pct > 60 else "✗"

    print(f"{metric.capitalize():<20} {actual_val:<15} {template_val:<15} {match_pct:>14.1f}% {status}")

# Calculate overall similarity
overall_match = np.mean([
    min(actual_stats['total'], template_stats['total']) / max(actual_stats['total'], template_stats['total']) * 100,
    min(actual_stats['top'], template_stats['top']) / max(actual_stats['top'], template_stats['top']) * 100,
    min(actual_stats['bottom'], template_stats['bottom']) / max(actual_stats['bottom'], template_stats['bottom']) * 100,
])

print(f"\n{'='*100}")
print(f"OVERALL EDGE PATTERN SIMILARITY: {overall_match:.1f}%")
print(f"{'='*100}")

# Create visual comparison
print(f"\n[STEP 5] Creating visual comparison...")

# Scale up for visibility
scale = 3

# Actual artifact
actual_large = cv2.resize(actual_enhanced, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
actual_color = cv2.cvtColor(actual_large, cv2.COLOR_GRAY2BGR)
cv2.rectangle(actual_color,
              (int(padding*scale), int((padding-5)*scale)),
              (int((padding+redaction_w)*scale), int((padding-5+redaction_h)*scale)),
              (0, 0, 255), 2)

# Template
template_large = cv2.resize(template_halo, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
template_color = cv2.cvtColor(template_large, cv2.COLOR_GRAY2BGR)
cv2.rectangle(template_color,
              (int(padding*scale), int((padding-5)*scale)),
              (int((padding+redaction_w)*scale), int((padding-5+redaction_h)*scale)),
              (0, 0, 255), 2)

# Add headers (text never overlays content)
actual_with_header = add_safe_header(actual_color, "ACTUAL ARTIFACT", header_height=50, text_color=(0, 200, 0), font_scale=0.7)
template_with_header = add_safe_header(template_color, f"EXPECTED: '{CANDIDATE_NAME}'", header_height=50, text_color=(0, 200, 0), font_scale=0.7)

# Edge comparison
actual_edges_large = cv2.resize(actual_edges_strong, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
actual_edges_color = cv2.cvtColor(actual_edges_large, cv2.COLOR_GRAY2BGR)
actual_edges_with_header = add_safe_header(actual_edges_color, "ACTUAL EDGES", header_height=50, text_color=(0, 200, 0), font_scale=0.7)

template_edges_large = cv2.resize(template_edges_strong, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
template_edges_color = cv2.cvtColor(template_edges_large, cv2.COLOR_GRAY2BGR)
template_edges_with_header = add_safe_header(template_edges_color, "EXPECTED EDGES", header_height=50, text_color=(0, 200, 0), font_scale=0.7)

# Combine with gutters
gutter_h = 30
gutter_v = 30

# Top row with gutter
gutter_h_img = np.ones((actual_with_header.shape[0], gutter_h, 3), dtype=np.uint8) * 255
top_row = np.hstack([actual_with_header, gutter_h_img, template_with_header])

# Bottom row with gutter
bottom_row = np.hstack([actual_edges_with_header, gutter_h_img, template_edges_with_header])

# Vertical gutter between rows
gutter_v_img = np.ones((gutter_v, top_row.shape[1], 3), dtype=np.uint8) * 255
combined = np.vstack([top_row, gutter_v_img, bottom_row])

# Calculate metrics for footer
width_match = max(0, 100 - abs(text_w - w) / w * 100)
combined_score = (width_match * 0.4) + (overall_match * 0.6)

# Determine assessment
if combined_score > 80:
    assessment = "STRONG MATCH"
    explanation = "Edge patterns and dimensions align closely with expected artifact pattern."
elif combined_score > 65:
    assessment = "MODERATE MATCH"
    explanation = "Some correlation in edge patterns, but not conclusive."
else:
    assessment = "WEAK MATCH"
    explanation = "Edge patterns do not strongly support this candidate."

# Add footer with metrics
footer_lines = [
    f"Width Match: {width_match:.1f}% | Edge Similarity: {overall_match:.1f}% | Combined: {combined_score:.1f}%",
    f"Assessment: {assessment} - {explanation}",
]
combined = add_multi_line_footer(combined, footer_lines, footer_height=70)

cv2.imwrite(f"{OUTPUT_DIR}/comparison.png", combined)

# Create difference map
diff = cv2.absdiff(actual_edges_strong, template_edges_strong)
diff_large = cv2.resize(diff, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
diff_color = cv2.cvtColor(diff_large, cv2.COLOR_GRAY2BGR)

# Add header (text never overlays content)
diff_with_header = add_safe_header(diff_color, "DIFFERENCE MAP (darker = better match)", header_height=50, text_color=(0, 200, 0), font_scale=0.7)
cv2.imwrite(f"{OUTPUT_DIR}/difference_map.png", diff_with_header)

print(f"  ✓ Comparison saved: {OUTPUT_DIR}/comparison.png")
print(f"  ✓ Difference map: {OUTPUT_DIR}/difference_map.png")

# Final assessment (already calculated above)
print(f"\n{'='*100}")
print(f"FORENSIC ASSESSMENT")
print(f"{'='*100}")

print(f"\nRedaction Location: ({x}, {y})")
print(f"Redaction Size: {w}x{h}px")
print(f"Candidate Text: '{CANDIDATE_NAME}'")
print(f"Expected Width: {text_w}px (actual: {w}px, diff: {abs(text_w-w)}px)")

print(f"Width Match: {width_match:.1f}%")
print(f"Edge Pattern Similarity: {overall_match:.1f}%")
print(f"Combined Confidence Score: {combined_score:.1f}%")

print(f"\nASSESSMENT: {assessment}")
print(f"Explanation: {explanation}")

print(f"\n{'='*100}")
print(f"Files for manual inspection:")
print(f"  {OUTPUT_DIR}/comparison.png - Side-by-side visual comparison")
print(f"  {OUTPUT_DIR}/difference_map.png - Shows where patterns differ")
print(f"{'='*100}")
