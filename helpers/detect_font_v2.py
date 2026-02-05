#!/usr/bin/env python3
"""
Better font detection - compares OCR measurements of VISIBLE text
against each font's theoretical measurements to find the best match.
"""

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from PIL import ImageFont
import os

FILE_PATH = "files/EFTA00037366.pdf"
FONTS_DIR = "fonts/fonts/"

print("="*100)
print("FONT DETECTION BY ANALYZING VISIBLE TEXT")
print("="*100)

# Load document
pages = convert_from_path(FILE_PATH)
img = np.array(pages[0])
img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

print(f"\n[*] Document: {FILE_PATH}")
print(f"[*] Image size: {img.shape[1]}x{img.shape[0]}px")

# Get OCR data with measurements
data = pytesseract.image_to_data(img_bgr, output_type=pytesseract.Output.DICT)

# Collect high-confidence text measurements
visible_text = []
for i in range(len(data['text'])):
    conf = int(data['conf'][i]) if data['conf'][i] != '-1' else 0
    text = data['text'][i].strip()
    w = data['width'][i]

    # Only use high-confidence, reasonably sized text
    if conf > 85 and len(text) >= 4 and len(text) <= 20 and w > 30:
        visible_text.append((text, w, conf))

print(f"\n[*] Found {len(visible_text)} high-confidence visible text samples")
print("\nSample visible text for font matching:")
print("-"*100)
for text, w, conf in visible_text[:15]:
    print(f"  '{text}' - {w:3d}px wide (confidence: {conf}%)")

# Test each font
font_files = sorted([f for f in os.listdir(FONTS_DIR) if f.endswith('.ttf') or f.endswith('.TTF')])

print(f"\n[*] Testing {len(font_files)} fonts against visible text...")
print("="*100)

results = []

for font_file in font_files:
    font_path = os.path.join(FONTS_DIR, font_file)

    # Test different font sizes
    for font_size in range(8, 19, 1):  # 8pt to 18pt
        try:
            font = ImageFont.truetype(font_path, font_size)

            # Calculate scale factors from multiple words
            scale_factors = []
            errors = []

            for text, actual_width, conf in visible_text:
                try:
                    theoretical_width = font.getlength(text)
                    if theoretical_width > 0:
                        sf = actual_width / theoretical_width
                        scale_factors.append(sf)
                except:
                    pass

            if len(scale_factors) < 5:
                continue  # Need at least 5 measurements

            # Calculate statistics
            avg_scale = sum(scale_factors) / len(scale_factors)
            std_dev = (sum((x - avg_scale) ** 2 for x in scale_factors) / len(scale_factors)) ** 0.5

            # Lower standard deviation = more consistent scaling = better font match
            results.append({
                'font': font_file,
                'size': font_size,
                'avg_scale': avg_scale,
                'std_dev': std_dev,
                'num_measurements': len(scale_factors),
                'consistency': (std_dev / avg_scale) * 100  # CV (coefficient of variation)
            })

        except Exception as e:
            pass

# Sort by consistency (lower coefficient of variation = better match)
results.sort(key=lambda x: x['consistency'])

print(f"\n{'Font':<25} {'Size':<6} {'Scale':<10} {'Std Dev':<12} {'Consistency':<15} {'Samples':<10} {'Ranking'}")
print("-"*100)

for i, r in enumerate(results[:20]):
    medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"#{i+1}"
    print(f"{r['font']:<25} {r['size']:<6} {r['avg_scale']:<10.4f} {r['std_dev']:<12.4f} {r['consistency']:<14.2f}% {r['num_measurements']:<10} {medal}")

if results:
    best = results[0]

    print(f"\n{'='*100}")
    print(f"DETECTED FONT: {best['font']} at {best['size']}pt")
    print(f"{'='*100}")
    print(f"  Scale Factor:      {best['avg_scale']:.4f}")
    print(f"  Standard Deviation: {best['std_dev']:.4f}")
    print(f"  Consistency:       {best['consistency']:.2f}% (lower = better)")
    print(f"  Measurements:      {best['num_measurements']} text samples")

    print(f"\nThis means:")
    print(f"  - Font used: {best['font']}")
    print(f"  - Point size: {best['size']}pt")
    print(f"  - Combined scaling factor (DPI + rendering): {best['avg_scale']:.4f}")
    print(f"  - A 100-unit theoretical width renders at {100 * best['avg_scale']:.1f} pixels in this document")

    # Show how well it matches visible text
    font = ImageFont.truetype(os.path.join(FONTS_DIR, best['font']), best['size'])

    print(f"\n{'='*100}")
    print("VALIDATION - Comparing predictions to actual OCR measurements:")
    print("="*100)

    print(f"{'Visible Text':<30} {'Actual (OCR)':<15} {'Predicted':<15} {'Error':<10} {'Status'}")
    print("-"*100)

    for text, actual_width, conf in visible_text[:20]:
        theoretical = font.getlength(text)
        predicted = theoretical * best['avg_scale']
        error = abs(predicted - actual_width)
        pct_error = (error / actual_width) * 100

        if pct_error < 2:
            status = "✓ Excellent"
        elif pct_error < 5:
            status = "✓ Good"
        elif pct_error < 10:
            status = "~ Fair"
        else:
            status = "✗ Poor"

        print(f"{text:<30} {actual_width:<15.1f} {predicted:<15.1f} {pct_error:>6.2f}% {status}")

    # Update main.py with detected font
    print(f"\n{'='*100}")
    print("RECOMMENDATION")
    print("="*100)
    print(f"Update main.py with:")
    print(f"  FONT_PATH = 'fonts/fonts/{best['font']}'")
    print(f"  font_size_pt = {best['size']}")
    print(f"  (This will automatically set scale factor to {best['avg_scale']:.4f})")
