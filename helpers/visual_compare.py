#!/usr/bin/env python3
"""
Visual Comparison - Show artifacts vs expected letter patterns.

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
from label_utils import add_safe_header, add_safe_footer

FILE_PATH = "files/EFTA00037366.pdf"
FONT_PATH = "fonts/fonts/times.ttf"
OUTPUT_DIR = "comparisons"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# The strong match we found
MATCH_NAME = "Jeffrey Epstein"
MATCH_X, MATCH_Y = 368, 3531
MATCH_W, MATCH_H = 713, 107

# Calibration
DPI_RATIO = 600 / 170
SCALE_FACTOR = 2.8998 * DPI_RATIO
FONT_SIZE = 12

print("="*100)
print(f"VISUAL COMPARISON: '{MATCH_NAME}' at ({MATCH_X}, {MATCH_Y})")
print("="*100)

# Load document at 600 DPI
print(f"\n[STEP 1] Loading document at 600 DPI...")
images = convert_from_path(FILE_PATH, dpi=600)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

# Extract the actual artifact region
print(f"\n[STEP 2] Extracting actual artifacts...")

padding = 15
roi_x = max(0, MATCH_X - padding)
roi_y = max(0, MATCH_Y - padding)
roi_w = min(gray.shape[1] - roi_x, MATCH_W + padding * 2)
roi_h = min(gray.shape[0] - roi_y, MATCH_H + padding * 2)

actual_roi = gray[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
actual_enhanced = cv2.normalize(actual_roi, None, 0, 255, cv2.NORM_MINMAX)

# Save actual artifact
cv2.imwrite(f"{OUTPUT_DIR}/01_actual_artifact.png", actual_enhanced)
print(f"  ✓ Saved: {OUTPUT_DIR}/01_actual_artifact.png")

# Extract just the edges from actual artifact
actual_edges = cv2.Canny(actual_enhanced, 30, 100)
cv2.imwrite(f"{OUTPUT_DIR}/02_actual_edges.png", actual_edges)
print(f"  ✓ Saved: {OUTPUT_DIR}/02_actual_edges.png")

# Create a template of what we expect
print(f"\n[STEP 3] Creating expected template for '{MATCH_NAME}'...")

scaled_font_size = int(FONT_SIZE * 600 / 72)
scaled_font = ImageFont.truetype(FONT_PATH, scaled_font_size)

template = Image.new('L', (roi_w, roi_h), 255)
draw = ImageDraw.Draw(template)

# Draw text
bbox = draw.textbbox((0, 0), MATCH_NAME, font=scaled_font)
text_w = bbox[2] - bbox[0]
text_h = bbox[3] - bbox[1]

draw.text((padding, (roi_h - text_h)//2), MATCH_NAME, font=scaled_font, fill=0)

# Convert to numpy
template_np = np.array(template)

# Apply a redaction box over it (simulate)
template_with_redaction = template_np.copy()
box_x = padding
box_y = (roi_h - text_h)//2 - 5
redaction_h = text_h + 10
cv2.rectangle(template_with_redaction, (box_x, box_y), (box_x + text_w, box_y + redaction_h), 0, -1)

# Extract halo from template
halo_mask = np.ones_like(template_with_redaction, dtype=np.uint8) * 255
halo_mask[box_y:box_y+redaction_h, box_x:box_x+text_w] = 0
template_halo = cv2.bitwise_and(template_with_redaction, template_with_redaction, mask=halo_mask)

# Save template
cv2.imwrite(f"{OUTPUT_DIR}/03_expected_template.png", template_np)
print(f"  ✓ Saved: {OUTPUT_DIR}/03_expected_template.png")

# Save template with redaction
cv2.imwrite(f"{OUTPUT_DIR}/04_template_with_redaction.png", template_with_redaction)
print(f"  ✓ Saved: {OUTPUT_DIR}/04_template_with_redaction.png")

# Extract edges from template
template_edges = cv2.Canny(template_halo, 50, 150)
cv2.imwrite(f"{OUTPUT_DIR}/05_expected_edges.png", template_edges)
print(f"  ✓ Saved: {OUTPUT_DIR}/05_expected_edges.png")

# Create side-by-side comparison
print(f"\n[STEP 4] Creating comparison images...")

# Resize for visibility
scale = 2
actual_large = cv2.resize(actual_enhanced, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
template_large = cv2.resize(template_halo, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)

# Convert to color
actual_color = cv2.cvtColor(actual_large, cv2.COLOR_GRAY2BGR)
template_color = cv2.cvtColor(template_large, cv2.COLOR_GRAY2BGR)

# Add headers (text never overlays content)
actual_with_header = add_safe_header(actual_color, "ACTUAL ARTIFACT", header_height=40, text_color=(0, 200, 0))
template_with_header = add_safe_header(template_color, "EXPECTED PATTERN", header_height=40, text_color=(0, 200, 0))

# Stack horizontally with gutter
gutter_width = 30
gutter = np.ones((actual_with_header.shape[0], gutter_width, 3), dtype=np.uint8) * 255
comparison = np.hstack([actual_with_header, gutter, template_with_header])
cv2.imwrite(f"{OUTPUT_DIR}/06_comparison.png", comparison)
print(f"  ✓ Saved: {OUTPUT_DIR}/06_comparison.png")

# Edge comparison
actual_edges_large = cv2.resize(actual_edges, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
template_edges_large = cv2.resize(template_edges, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)

actual_edges_color = cv2.cvtColor(actual_edges_large, cv2.COLOR_GRAY2BGR)
template_edges_color = cv2.cvtColor(template_edges_large, cv2.COLOR_GRAY2BGR)

# Add headers (text never overlays content)
actual_edges_with_header = add_safe_header(actual_edges_color, "ACTUAL EDGES", header_height=40, text_color=(0, 200, 0))
template_edges_with_header = add_safe_header(template_edges_color, "EXPECTED EDGES", header_height=40, text_color=(0, 200, 0))

# Stack horizontally with gutter
gutter = np.ones((actual_edges_with_header.shape[0], gutter_width, 3), dtype=np.uint8) * 255
edge_comparison = np.hstack([actual_edges_with_header, gutter, template_edges_with_header])
cv2.imwrite(f"{OUTPUT_DIR}/07_edge_comparison.png", edge_comparison)
print(f"  ✓ Saved: {OUTPUT_DIR}/07_edge_comparison.png")

print(f"\n{'='*100}")
print(f"ANALYSIS COMPLETE")
print(f"{'='*100}")
print(f"\nComparison images saved to: {OUTPUT_DIR}/")
print(f"\nKey files to examine:")
print(f"  01_actual_artifact.png    - The actual artifact from the document")
print(f"  02_actual_edges.png       - Edge detection of actual artifact")
print(f"  05_expected_edges.png     - Edges we expect for '{MATCH_NAME}'")
print(f"  07_edge_comparison.png    - Side-by-side edge comparison")
print(f"\nIf the edge patterns match closely, it suggests '{MATCH_NAME}' is the redacted text.")
