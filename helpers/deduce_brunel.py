#!/usr/bin/env python3
"""Deduce name in 'Attempts were made to [NAME] and Brunel'"""

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import ImageFont, ImageDraw
import pytesseract
import os

FILE_PATH = "files/EFTA00037366.pdf"
FONT_PATH = "fonts/fonts/times.ttf"

print("="*100)
print("FORENSIC ANALYSIS: 'Attempts were made to [REDACTED] and Brunel'")
print("="*100)

# Load
images = convert_from_path(FILE_PATH, dpi=1200)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

# Find words
data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

attempts_pos = None
brunel_pos = None

for i in range(len(data['text'])):
    text = data['text'][i].strip()
    if 'Brunel' in text and data['conf'][i] > 70:
        brunel_pos = (data['left'][i], data['top'][i], data['width'][i])
        print(f"Found 'Brunel' at: {brunel_pos}")

# Find the word before it (should be "to")
for i in range(len(data['text'])):
    text = data['text'][i].strip()
    if 'to' in text and data['conf'][i] > 70:
        # Check if "Brunel" comes after this
        x_pos = data['left'][i]
        if brunel_pos and x_pos < brunel_pos[0] - 100 and x_pos > brunel_pos[0] - 500:
            attempts_pos = (x_pos, data['top'][i], data['width'][i])
            print(f"Found 'to' at: {attempts_pos}")
            break

# Find redactions between them
if attempts_pos and brunel_pos:
    print(f"\nLooking for redactions between x={attempts_pos[0]} and x={brunel_pos[0]}...")
    
    _, black_mask = cv2.threshold(gray, 5, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if attempts_pos[0] < x < brunel_pos[0]:
            print(f"Found redaction at ({x}, {y}), size: {w}x{h}px")
            
            # Analyze
            font_size = int(12 * 1200 / 72)
            font = ImageFont.truetype(FONT_PATH, font_size)
            
            CANDIDATES = ["Sarah", "Kellen", "Ghislaine", "Nadia", "Lesley", "Jeffrey", "Epstein", "Bill", "Clinton", "Prince", "Andrew", "Emmy", "Taylor"]
            
            print(f"\nWidth analysis:")
            for name in CANDIDATES:
                expected = font.getlength(name)
                diff = abs(expected - w)
                pct = diff / expected * 100
                
                match = "✓" if diff < expected * 0.15 else "  "
                print(f"  {name:12s} {expected:7.1f}px  actual: {w:4d}px  diff: {diff:6.1f}px ({pct:5.1f}%) {match}")
