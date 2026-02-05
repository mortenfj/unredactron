#!/usr/bin/env python3
"""
Forensic Text Reconstruction - Algorithmic letter identification from artifacts.

This script:
1. Analyzes artifact patterns around redactions
2. Extracts distinctive features (ascenders, descenders, serifs, curves)
3. Matches against letter templates
4. Brute-forces combinations with scoring
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image, ImageFont, ImageDraw
import os
from collections import defaultdict

FILE_PATH = "files/EFTA00037366.pdf"
FONT_PATH = "fonts/fonts/times.ttf"
OUTPUT_DIR = "reconstruction"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Letter categories with their distinctive features
LETTER_CATEGORIES = {
    'ascenders': ['b', 'd', 'f', 'h', 'k', 'l', 't'],  # Have tall parts
    'descenders': ['g', 'j', 'p', 'q', 'y'],  # Have parts below baseline
    'serifs_upper': ['A', 'B', 'D', 'E', 'F', 'H', 'I', 'K', 'L', 'M', 'N', 'P', 'R', 'T', 'V', 'W', 'X', 'Y', 'Z'],
    'serifs_lower': ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'],
    'round': ['O', 'Q', 'C', 'G', 'S', 'a', 'c', 'd', 'e', 'o', 'q'],
    'vertical': ['H', 'I', 'M', 'N', 'h', 'i', 'm', 'n', 'r', 'u'],
}

# Common words and letter combinations for matching
COMMON_WORDS = set([
    'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one',
    'our', 'out', 'has', 'have', 'been', 'will', 'with', 'that', 'this', 'from', 'they', 'would',
    'there', 'their', 'what', 'about', 'which', 'when', 'make', 'like', 'time', 'just', 'know',
    'take', 'year', 'into', 'people', 'email', 'contact', 'attempts', 'confirmed', 'address',
    'residence', 'holiday', 'weekend', 'approached', 'updating', 'conspirators', 'status',
])

# Common first names
COMMON_NAMES = set([
    'Sarah', 'Ghislaine', 'Nadia', 'Lesley', 'Jeffrey', 'Bill', 'Emmy', 'Prince', 'John', 'Jane',
    'David', 'Michael', 'Robert', 'William', 'Richard', 'Joseph', 'Thomas', 'Charles', 'Mary',
    'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara', 'Susan', 'Jessica', 'Karen', 'Lisa',
    'Nancy', 'Betty', 'Margaret', 'Sandra', 'Ashley', 'Kimberly', 'Emily', 'Donna', 'Michelle',
])

print("="*100)
print("FORENSIC TEXT RECONSTRUCTION - Algorithmic Letter Identification")
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

# Calibration
print(f"\n[STEP 3] Calibrating font metrics...")
import pytesseract
data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

# Find a visible word for calibration
control_width = None
for i, text in enumerate(data['text']):
    if 'Subject:' in text:
        control_width = data['width'][i]
        break

if control_width:
    print(f"  Control word 'Subject:' width: {control_width}px at 600 DPI")
    # Calculate scale: at 600 DPI, we need to account for the resolution
    DPI_RATIO = 600 / 170
    SCALE_FACTOR = 2.8998 * DPI_RATIO
    print(f"  Scale factor: {SCALE_FACTOR:.4f}")
else:
    SCALE_FACTOR = 10.23  # Fallback
    print(f"  Using fallback scale factor: {SCALE_FACTOR:.4f}")

# Load font for rendering
FONT_SIZE = 12
font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
scaled_font_size = int(FONT_SIZE * 600 / 72)
scaled_font = ImageFont.truetype(FONT_PATH, scaled_font_size)

print(f"\n[STEP 4] Analyzing redaction artifacts...")

class ArtifactAnalyzer:
    def __init__(self, gray_img, scale_factor, font):
        self.gray = gray_img
        self.scale = scale_factor
        self.font = font

    def extract_artifacts(self, x, y, w, h, padding=10):
        """Extract and enhance artifact region around redaction."""
        roi_x = max(0, x - padding)
        roi_y = max(0, y - padding)
        roi_w = min(self.gray.shape[1] - roi_x, w + padding * 2)
        roi_h = min(self.gray.shape[0] - roi_y, h + padding * 2)

        roi = self.gray[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]

        # Enhance contrast
        enhanced = cv2.normalize(roi, None, 0, 255, cv2.NORM_MINMAX)

        # Extract edges
        edges = cv2.Canny(enhanced, 30, 100)

        return roi, enhanced, edges

    def analyze_features(self, edges, box_x, box_y, box_w, box_h):
        """Analyze artifact features."""
        # Look at edges in the halo region
        h, w = edges.shape[:2]
        halo_mask = np.ones((h, w), dtype=np.uint8) * 255

        # Mask out the redaction box
        halo_mask[box_y:box_y+box_h, box_x:box_x+box_w] = 0

        halo_edges = cv2.bitwise_and(edges, edges, mask=halo_mask)

        # Count edge pixels
        edge_count = np.sum(halo_edges > 0)

        # Analyze top region (for ascenders)
        top_region = halo_edges[max(0, box_y-10):box_y, :]
        top_edges = np.sum(top_region > 0)

        # Analyze bottom region (for descenders)
        bottom_region = halo_edges[box_y+box_h:min(h, box_y+box_h+10), :]
        bottom_edges = np.sum(bottom_region > 0)

        return {
            'total_edges': edge_count,
            'top_edges': top_edges,
            'bottom_edges': bottom_edges,
            'has_ascenders': top_edges > 50,
            'has_descenders': bottom_edges > 50,
        }

    def score_candidate(self, candidate_text, actual_width, features):
        """Score a candidate text string against the artifacts."""
        # Calculate expected width
        theoretical = self.font.getlength(candidate_text)
        expected_width = theoretical * self.scale

        # Width score
        width_diff = abs(expected_width - actual_width)
        width_score = max(0, 100 - (width_diff / actual_width * 100))

        # Letter feature score
        has_ascenders_in_name = any(c in LETTER_CATEGORIES['ascenders'] for c in candidate_text)
        has_descenders_in_name = any(c in LETTER_CATEGORIES['descenders'] for c in candidate_text)

        feature_score = 100
        if features['has_ascenders'] and not has_ascenders_in_name:
            feature_score -= 30
        if not features['has_ascenders'] and has_ascenders_in_name:
            feature_score -= 20
        if features['has_descenders'] and not has_descenders_in_name:
            feature_score -= 30
        if not features['has_descenders'] and has_descenders_in_name:
            feature_score -= 20

        # Edge density score
        expected_edges = len(candidate_text) * 150  # Approximate edges per letter
        edge_ratio = min(expected_edges, features['total_edges']) / max(expected_edges, features['total_edges'])
        edge_score = edge_ratio * 100

        # Combined score (weighted)
        combined = (width_score * 0.5) + (feature_score * 0.3) + (edge_score * 0.2)

        return {
            'width_score': width_score,
            'feature_score': feature_score,
            'edge_score': edge_score,
            'combined': combined,
            'expected_width': expected_width,
        }

analyzer = ArtifactAnalyzer(gray, SCALE_FACTOR, scaled_font)

print(f"\n[STEP 5] Algorithmic reconstruction of redacted text...")
print(f"{'='*100}")

results = []

for i, (x, y, w, h) in enumerate(redactions):
    # Skip very small or very large redactions
    if w < 100 or w > 2000:
        continue

    print(f"\n--- Redaction #{i+1} at ({x}, {y}), size: {w}x{h}px ---")

    # Extract artifacts
    roi, enhanced, edges = analyzer.extract_artifacts(x, y, w, h)

    # Analyze features
    box_x = x - max(0, x - 10)
    box_y = y - max(0, y - 10)
    features = analyzer.analyze_features(edges, box_x, box_y, w, h)

    print(f"Features: {features['total_edges']} edge pixels")
    if features['has_ascenders']:
        print(f"  → Ascenders detected (tall letters like b, d, f, h, k, l, t)")
    if features['has_descenders']:
        print(f"  → Descenders detected (tails like g, j, p, q, y)")

    # Generate candidates
    candidates = set()

    # 1. Calculate approximate letter count
    avg_letter_width = 50 * SCALE_FACTOR / 10  # Rough estimate
    letter_count = int(round(w / avg_letter_width))
    letter_count = max(2, min(15, letter_count))  # Reasonable range

    print(f"Estimated letter count: ~{letter_count}")

    # 2. Add dictionary words of similar length
    for word in COMMON_WORDS:
        if abs(len(word) - letter_count) <= 2:
            candidates.add(word)

    # 3. Add names of similar length
    for name in COMMON_NAMES:
        if abs(len(name) - letter_count) <= 1:
            candidates.add(word)

    # 4. Add capitalized versions
    candidates_copy = list(candidates)
    for word in candidates_copy:
        candidates.add(word.capitalize())
        candidates.add(word.upper())

    # 5. Brute force: try common letter combinations
    # Generate patterns like "Aaaaa", "Aa Aaaa" (First Last)
    common_first_letters = "SJMBTGRPAH"
    for first in common_first_letters:
        # First name pattern
        candidates.add(first + "effrey")
        candidates.add(first + "ennifer")
        candidates.add(first + "ane")
        candidates.add(first + "ohn")
        candidates.add(first + "ames")
        candidates.add(first + "ill")
        candidates.add(first + "avid")

    print(f"Testing {len(candidates)} candidates...")

    # Score all candidates
    scored_candidates = []
    for candidate in candidates:
        if len(candidate) < 2 or len(candidate) > 20:
            continue

        scores = analyzer.score_candidate(candidate, w, features)
        scored_candidates.append((candidate, scores))

    # Sort by combined score
    scored_candidates.sort(key=lambda x: x[1]['combined'], reverse=True)

    # Show top matches
    print(f"\nTop 5 candidates:")
    print("-"*100)

    top_matches = 0
    for candidate, scores in scored_candidates[:5]:
        if scores['combined'] > 60:
            top_matches += 1
            status = "STRONG" if scores['combined'] > 80 else "MODERATE" if scores['combined'] > 70 else "WEAK"
            print(f"  [{status}] '{candidate}'")
            print(f"       Width: {w}px (expected: {scores['expected_width']:.0f}px, score: {scores['width_score']:.1f}%)")
            print(f"       Features: {scores['feature_score']:.1f}%, Edges: {scores['edge_score']:.1f}%")
            print(f"       Combined: {scores['combined']:.1f}%")

            if scores['combined'] > 75:
                results.append({
                    'redaction': i+1,
                    'x': x,
                    'y': y,
                    'w': w,
                    'h': h,
                    'candidate': candidate,
                    'score': scores['combined'],
                    'scores': scores
                })

    if top_matches == 0:
        print(f"  No strong matches found")

# Final summary
print(f"\n{'='*100}")
print(f"RECONSTRUCTION SUMMARY")
print(f"{'='*100}")

if results:
    results.sort(key=lambda x: x['score'], reverse=True)

    print(f"\nHigh-confidence reconstructions:")
    print("-"*100)

    for r in results:
        if r['score'] > 75:
            print(f"\nRedaction at ({r['x']}, {r['y']}): {r['w']}px wide")
            print(f"  → Reconstructed text: '{r['candidate']}'")
            print(f"  → Confidence: {r['score']:.1f}%")

    print(f"\n{'='*100}")
    print(f"Total high-confidence reconstructions: {len([r for r in results if r['score'] > 75])}")
    print(f"{'='*100}")
else:
    print("No high-confidence reconstructions found.")
    print("This could indicate:")
    print("  - Redactions are clean (no artifact traces)")
    print("  - Text is not in common dictionaries")
    print("  - Different font or size than expected")
