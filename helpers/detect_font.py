#!/usr/bin/env python3
"""
Automatic font detection - tests all fonts and finds the best match.
Reports font, scale factor, and spacing metrics.
"""

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from PIL import ImageFont
import os

FILE_PATH = "files/EFTA00037366.pdf"
FONTS_DIR = "fonts/fonts/"

# Test names
TEST_NAMES = [
    "Bill Clinton",
    "JEFFREY EPSTEIN",
    "GHISLAINE MAXWELL",
    "Sarah Kellen",
]

print("="*100)
print("AUTOMATIC FONT DETECTION")
print("="*100)

# Load document
pages = convert_from_path(FILE_PATH)
img = np.array(pages[0])
img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

print(f"\n[*] Document: {FILE_PATH}")
print(f"[*] Pages: {len(pages)}")
print(f"[*] Image size: {img.shape[1]}x{img.shape[0]}px")

# Get control word from OCR
data = pytesseract.image_to_data(img_bgr, output_type=pytesseract.Output.DICT)

# Find a good control word (short, confident detection)
print(f"\n[*] Scanning for control words...")
control_words = []
for i, text in enumerate(data['text']):
    conf = int(data['conf'][i]) if data['conf'][i] != '-1' else 0
    text_clean = text.strip()
    if conf > 80 and 5 <= len(text_clean) <= 15 and text_clean[0].isupper():
        w = data['width'][i]
        h = data['height'][i]
        control_words.append((text_clean, w, h, conf))

# Show top control words
print(f"\n[*] Found {len(control_words)} potential control words:")
print("-"*100)
for word, w, h, conf in control_words[:10]:
    print(f"  '{word}' - {w:3d}x{h:2d}px (confidence: {conf}%)")

# Use the best control word
CONTROL_WORD = control_words[0][0]
CONTROL_WIDTH = control_words[0][1]
CONTROL_HEIGHT = control_words[0][2]

print(f"\n[*] Selected control word: '{CONTROL_WORD}' ({CONTROL_WIDTH}px wide)")

# Find redactions
gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

redactions = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if w > 30 and h > 10 and w/h > 1.5:
        redactions.append((x, y, w, h))

print(f"[*] Found {len(redactions)} redaction blocks")

# Get all font files
font_files = sorted([f for f in os.listdir(FONTS_DIR) if f.endswith('.ttf') or f.endswith('.TTF')])

print(f"\n[*] Testing {len(font_files)} fonts...")
print("="*100)

results = []

for font_file in font_files:
    font_path = os.path.join(FONTS_DIR, font_file)

    try:
        # Test at different sizes
        for font_size in [10, 11, 12, 13, 14]:
            font = ImageFont.truetype(font_path, font_size)

            # Calculate scale factor from control word
            control_theoretical = font.getlength(CONTROL_WORD)
            scale_factor = CONTROL_WIDTH / control_theoretical

            # Test against redaction widths
            total_error = 0
            tests = 0
            close_matches = 0

            for x, y, w, h in redactions:
                for name in TEST_NAMES:
                    predicted = font.getlength(name) * scale_factor
                    error = abs(predicted - w)
                    total_error += error
                    tests += 1
                    if error <= 15:
                        close_matches += 1

            avg_error = total_error / tests
            match_rate = (close_matches / tests) * 100

            results.append({
                'font': font_file,
                'size': font_size,
                'scale_factor': scale_factor,
                'avg_error': avg_error,
                'match_rate': match_rate,
                'close_matches': close_matches,
                'tests': tests
            })

    except Exception as e:
        pass

# Sort by average error (lower is better)
results.sort(key=lambda x: x['avg_error'])

print(f"\n{'Font':<25} {'Size':<6} {'Scale':<10} {'Avg Error':<12} {'Match Rate':<12} {'Ranking'}")
print("-"*100)

for i, r in enumerate(results[:15]):
    medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"#{i+1}"
    print(f"{r['font']:<25} {r['size']:<6} {r['scale_factor']:<10.4f} {r['avg_error']:<12.2f}px {r['match_rate']:<11.1f}% {medal}")

if results:
    best = results[0]
    print(f"\n{'='*100}")
    print(f"RECOMMENDED FONT: {best['font']} at {best['size']}pt")
    print(f"{'='*100}")
    print(f"  Scale Factor:      {best['scale_factor']:.4f}")
    print(f"  Average Error:     {best['avg_error']:.2f}px")
    print(f"  Match Rate:        {best['match_rate']:.1f}% ({best['close_matches']}/{best['tests']} tests)")
    print(f"\nThis scale factor combines:")
    print(f"  - Document DPI/resolution")
    print(f"  - Font rendering size")
    print(f"  - Letter spacing (tracking)")
    print(f"  - Any kerning adjustments")

    # Detailed spacing analysis
    print(f"\n{'='*100}")
    print("SPACING ANALYSIS")
    print("="*100)

    font = ImageFont.truetype(os.path.join(FONTS_DIR, best['font']), best['size'])
    scale_factor = best['scale_factor']

    # Analyze character widths
    test_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    print(f"\nCharacter widths at {best['size']}pt (scaled to document):")
    print("-"*60)

    char_widths = {}
    for char in test_chars:
        theoretical = font.getlength(char)
        scaled = theoretical * scale_factor
        char_widths[char] = scaled

    # Show a sample
    for char in "ABCDEFGHIJ":
        print(f"  '{char}': {char_widths[char]:.2f}px")

    print("\nSample name width predictions:")
    print("-"*60)
    for name in TEST_NAMES[:3]:
        theoretical = font.getlength(name)
        scaled = theoretical * scale_factor
        print(f"  '{name}': {scaled:.1f}px")
