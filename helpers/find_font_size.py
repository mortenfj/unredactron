#!/usr/bin/env python3
"""
Test different font sizes to find the best match.
"""

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from PIL import ImageFont

FILE_PATH = "files/EFTA00513855.pdf"
FONT_PATH = "fonts/fonts/times.ttf"
CONTROL_WORD = "Contacts"

# Test names
TEST_NAMES = [
    "JEFFREY EPSTEIN",
    "GHISLAINE MAXWELL",
    "Sarah Kellen",
    "Bill Clinton",
]

# Load and calibrate
pages = convert_from_path(FILE_PATH)
img = np.array(pages[0])
img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

# Get calibration data
data = pytesseract.image_to_data(img_bgr, output_type=pytesseract.Output.DICT)
target_box = None
for i, text in enumerate(data['text']):
    if CONTROL_WORD.lower() in text.lower():
        target_box = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
        break

control_width_px = target_box[2]
control_height_px = target_box[3]

print(f"OCR detected '{CONTROL_WORD}' at {control_width_px}x{control_height_px}px")
print(f"\nTesting different font sizes...")
print("="*100)

# Find redactions
gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

redactions = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if w > 30 and h > 10 and w/h > 1.5:
        redactions.append((x, y, w, h))
redactions.sort(key=lambda b: b[1])

test_redactions = [282, 400, 107]  # A few different sizes

results = []

for font_size in range(8, 19, 1):  # Test 8pt to 18pt
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)

        # The control word in this font size
        control_theoretical = font.getlength(CONTROL_WORD)

        # Scale factor
        scale_factor = control_width_px / control_theoretical

        # Test predictions
        total_error = 0
        tests = 0

        for redaction_width in test_redactions:
            for name in TEST_NAMES:
                predicted = font.getlength(name) * scale_factor
                error = abs(predicted - redaction_width)
                total_error += error
                tests += 1

        avg_error = total_error / tests

        # Also check how close the font size height is
        # Get font metrics
        try:
            font_size_metric = font.size  # This is the point size we set
        except:
            font_size_metric = font_size

        results.append((font_size, avg_error, scale_factor))

    except Exception as e:
        pass

results.sort(key=lambda x: x[1])

print(f"\n{'Font Size':<12} {'Avg Error (px)':<18} {'Scale Factor':<15} {'Ranking'}")
print("-"*100)

for i, (font_size, avg_error, scale_factor) in enumerate(results[:5]):
    medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"#{i+1}"
    print(f"{font_size:<12} {avg_error:<18.2f} {scale_factor:<15.4f} {medal}")

if results:
    best = results[0]
    print(f"\n{'='*100}")
    print(f"BEST MATCH: {best[0]}pt font")
    print(f"Average error: {best[1]:.2f}px")
    print(f"Scale factor: {best[2]:.4f}")
    print(f"{'='*100}")

    # Now test with the best font size and show predictions vs actual
    print(f"\nDetailed analysis with {best[0]}pt font:")
    print("-"*100)

    font = ImageFont.truetype(FONT_PATH, best[0])
    scale_factor = best[2]

    for redaction_width in test_redactions:
        print(f"\nRedaction width: {redaction_width}px")
        print(f"{'Name':<30} {'Predicted':>12} {'Error':>10}")
        for name in TEST_NAMES:
            predicted = font.getlength(name) * scale_factor
            error = abs(predicted - redaction_width)
            status = "✓ CLOSE" if error < 15 else ""
            print(f"  {name:<30} {predicted:>10.1f}px   {error:>+6.1f}px  {status}")
