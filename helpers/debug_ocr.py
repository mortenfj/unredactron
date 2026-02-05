#!/usr/bin/env python3
"""
Debug script to see what OCR detects on the first page of the PDF.
"""

import pytesseract
import numpy as np
from pdf2image import convert_from_path
import cv2

FILE_PATH = "files/EFTA00037366.pdf"

print(f"Loading {FILE_PATH}...")
pages = convert_from_path(FILE_PATH)
print(f"Loaded {len(pages)} pages")

# Convert first page
img = np.array(pages[0])
img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

print(f"\nPage 1 size: {img.shape[1]}x{img.shape[0]}px")
print("\nRunning OCR to find all text...")

# Get OCR data with bounding boxes
data = pytesseract.image_to_data(img_bgr, output_type=pytesseract.Output.DICT)

print(f"\nFound {len(data['text'])} text elements")
print("\n" + "="*60)
print("DETECTED TEXT (with confidence and position):")
print("="*60)

# Print all detected text with confidence
found_words = []
for i in range(len(data['text'])):
    text = data['text'][i].strip()
    conf = int(data['conf'][i]) if data['conf'][i] != '-1' else 0

    if text and conf > 30:  # Only show confident detections
        x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
        found_words.append(text)
        print(f"  [{conf:3d}%] '{text}' at ({x:4d},{y:4d}) size: {w:3d}x{h:3d}px")

print("\n" + "="*60)
print("SUMMARY OF ALL DETECTED WORDS:")
print("="*60)
print(' '.join(found_words[:100]))  # First 100 words

print("\n" + "="*60)
print("POTENTIAL CONTROL WORDS (short, common words):")
print("="*60)
# Look for short words that might be good for calibration
potential_controls = set()
for word in found_words:
    if 4 <= len(word) <= 10 and word[0].isupper():
        potential_controls.add(word)

for word in sorted(potential_controls):
    print(f"  - {word}")
