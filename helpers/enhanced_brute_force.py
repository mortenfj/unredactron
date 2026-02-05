#!/usr/bin/env python3
"""
Enhanced Brute Force - Parse CSV properly, extract all name variants,
and weight by CSV confidence markers (+, ?, ~)
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import ImageFont
import csv
import re

FILE_PATH = "files/EFTA00037366.pdf"
FONT_PATH = "fonts/fonts/times.ttf"

print("="*120)
print("ENHANCED BRUTE FORCE - Parse CSV with name variants and confidence scores")
print("="*120)

# Parse the malformed CSV more carefully
name_entries = []

with open('names.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip header/empty lines
        if not line or line.startswith('EFTA') or line.startswith('Name') or line.isdigit():
            i += 1
            continue

        # Skip note-only lines
        if line.startswith('"') or line.startswith('Deceased') or line.startswith('Former') or \
           line.startswith('Note:') or line.startswith('Owner') or line.startswith('Primary') or \
           line.startswith('State-licensed') or line.startswith('Current') or line.startswith('Close'):
            i += 1
            continue

        # Extract name and data
        parts = line.split('\t')
        if len(parts) > 1:
            name_raw = parts[0].strip()

            # Skip if it's just a number or note
            if not name_raw or name_raw.isdigit() or len(name_raw) < 2:
                i += 1
                continue

            # Clean up name
            name = re.sub(r'\s*\([^)]*\)', '', name_raw)  # Remove parentheses
            name = re.sub(r'\s*"[^"]*"', '', name)  # Remove quotes
            name = name.strip()

            if not name or len(name) < 2:
                i += 1
                continue

            # Extract confidence markers from the rest of the row
            # Count +, ?, ~ markers
            confidence = 0
            if len(parts) > 1:
                for part in parts[1:]:
                    if '+' in part:
                        confidence += part.count('+')
                    if '?' in part:
                        confidence += part.count('?') * 0.5
                    if '~' in part:
                        confidence += part.count('~') * 0.3

            # Generate name variants
            variants = set()

            # Full name as-is
            variants.add(name)

            # Split by common separators
            for sep in ['/', ' or ', ' aka ', ',']:
                if sep in name.lower():
                    parts_split = name.split(sep)
                    for p in parts_split:
                        p = p.strip()
                        if p:
                            variants.add(p)

                            # Also extract all individual words from each variant
                            words_in_variant = p.split()
                            for w in words_in_variant:
                                if len(w) > 2:
                                    variants.add(w)

                            # Extract last 2-3 words for compound surnames
                            if len(words_in_variant) >= 2:
                                # Last 2 words
                                variants.add(' '.join(words_in_variant[-2:]))
                            if len(words_in_variant) >= 3:
                                # Last 3 words
                                variants.add(' '.join(words_in_variant[-3:]))

            # Extract all words from original name
            for word in name.split():
                if len(word) > 2:
                    variants.add(word)

            # Extract last name(s) from original
            if ' ' in name:
                words = name.split()
                # Last word
                variants.add(words[-1])
                # Last 2 words
                if len(words) >= 2:
                    variants.add(' '.join(words[-2:]))
                # Last 3 words
                if len(words) >= 3:
                    variants.add(' '.join(words[-3:]))

            # Remove very short variants
            variants = {v for v in variants if len(v) > 2}

            # Store entry
            entry = {
                'name_raw': name_raw,
                'variants': list(variants),
                'confidence': confidence
            }
            name_entries.append(entry)

        i += 1

# Collect all unique variants
all_variants = []
for entry in name_entries:
    for variant in entry['variants']:
        all_variants.append({
            'variant': variant,
            'confidence': entry['confidence'],
            'source': entry['name_raw']
        })

# Remove duplicates (keep highest confidence)
variant_map = {}
for item in all_variants:
    v = item['variant']
    if v not in variant_map or item['confidence'] > variant_map[v]['confidence']:
        variant_map[v] = item

# Sort by confidence
CANDIDATES = sorted(variant_map.values(), key=lambda x: x['confidence'], reverse=True)

print(f"\nExtracted {len(CANDIDATES)} unique name variants from {len(name_entries)} raw entries")
print(f"\nTop 20 candidates by CSV confidence:")
for i, c in enumerate(CANDIDATES[:20], 1):
    conf_mark = '+' * int(c['confidence']) if c['confidence'] >= 1 else ''
    print(f"  {i:2d}. {c['variant']:<35} confidence: {c['confidence']:4.1f} {conf_mark}")

# Load PDF
print(f"\nLoading PDF at 1200 DPI...")
images = convert_from_path(FILE_PATH, dpi=1200)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

# Load font
font_size = int(12 * 1200 / 72)
font = ImageFont.truetype(FONT_PATH, font_size)

# Find redactions
print(f"Finding redactions...")
_, black_mask = cv2.threshold(gray, 5, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

redactions = [(x, y, w, h) for cnt in contours for x, y, w, h in [cv2.boundingRect(cnt)] if w > 200 and h > 100]

print(f"Found {len(redactions)} significant redactions")
print(f"Testing {len(redactions)} × {len(CANDIDATES)} = {len(redactions) * len(CANDIDATES):,} combinations\n")

# Analyze each redaction
best_matches = []
for i, (x, y, w, h) in enumerate(redactions):
    best_candidate = None
    best_error = 100
    best_confidence = -1
    best_raw_error = 100

    for item in CANDIDATES:
        candidate = item['variant']
        confidence = item['confidence']

        expected_width = font.getlength(candidate)
        diff = abs(expected_width - w)
        pct_error = diff / expected_width * 100 if expected_width > 0 else 100

        # Combined score: width match is PRIMARY, CSV confidence is SECONDARY
        # Use confidence as tie-breaker (divided by 10 so it doesn't override width)
        combined_score = pct_error - (confidence / 10)

        if combined_score < best_error or (abs(combined_score - best_error) < 0.1 and confidence > best_confidence):
            best_error = combined_score
            best_candidate = candidate
            best_confidence = confidence
            best_expected = expected_width
            best_diff = diff
            best_raw_error = pct_error

    if best_candidate is not None and best_raw_error < 30:  # Only keep reasonable matches
        best_matches.append({
            'rank': i + 1,
            'position': (x, y),
            'size': (w, h),
            'candidate': best_candidate,
            'confidence': best_confidence,
            'expected': best_expected,
            'actual': w,
            'diff': best_diff,
            'error': best_raw_error,
            'letters': len(best_candidate.replace(" ", ""))
        })

# Sort by combined score (which is best_error)
best_matches.sort(key=lambda m: m['error'])

# Display top matches
print(f"{'='*120}")
print(f"TOP 20 UNIQUE REDACTIONS (CSV-weighted)")
print(f"{'='*120}")
print(f"\nRank  {'Detected Name':<30} {'Position':<18} {'Size':<12} {'Width':<12} {'Diff':<10} {'Error':<8} {'Conf':<6} {'Letters'}")
print("-"*145)

for i, match in enumerate(best_matches[:20], 1):
    pos_str = f"({match['position'][0]}, {match['position'][1]})"
    size_str = f"{match['size'][0]}x{match['size'][1]}"

    # Confidence markers
    conf_display = '+' * int(match['confidence']) if match['confidence'] >= 1 else ''

    # Rating
    if match['error'] < 1:
        rating = "★★★"
    elif match['error'] < 5:
        rating = "★★"
    elif match['error'] < 10:
        rating = "★"
    else:
        rating = ""

    print(f"{i:<5} {match['candidate']:<30} {pos_str:<18} {size_str:<12} "
          f"{match['expected']:>8.1f}px  {match['diff']:>6.1f}px   "
          f"{match['error']:>5.1f}%   {conf_display:<5} {match['letters']:>3}  {rating}")

print("="*120)

# Check for Marcinkova
print(f"\nSearching for 'Marcinkova' variants...")
found_marcinkova = False
for match in best_matches:
    if 'marcinko' in match['candidate'].lower():
        print(f"  ✓ Found: {match['candidate']} at {match['position']} - {match['error']:.2f}% error (confidence: {match['confidence']})")
        found_marcinkova = True

if not found_marcinkova:
    # Check all candidates
    for item in CANDIDATES:
        if 'marcinko' in item['variant'].lower():
            print(f"  Marcinkova variants in list: {item['variant']} (confidence: {item['confidence']})")
            # Test it manually
            width = font.getlength(item['variant'])
            print(f"    Width would be: {width:.1f}px")

print("="*120)
