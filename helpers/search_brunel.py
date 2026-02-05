#!/usr/bin/env python3
"""Search for any occurrence of 'Brunel' or find the redaction near 'Attempts'"""

import cv2
import numpy as np
from pdf2image import convert_from_path
import pytesseract

FILE_PATH = "files/EFTA00037366.pdf"

# Load at 1200 DPI
images = convert_from_path(FILE_PATH, dpi=1200)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

# Get OCR
data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

print("Searching for 'Brunel' or the redaction after 'were made to'...")

# Find "Attempts were made to"
were_made_to = None
for i in range(len(data['text'])):
    text = data['text'][i].strip()
    if 'were' in text and 'made' in text and 'to' in text:
        if data['conf'][i] > 80:
            x, y = data['left'][i], data['top'][i]
            print(f"Found 'were made to' at ({x}, {y})")
            were_made_to = (x, y, data['width'][i])

            # Look for next few words to find the redaction
            for j in range(i+1, min(i+10, len(data['text']))):
                next_x = data['left'][j]
                next_text = data['text'][j].strip()
                next_conf = data['conf'][j]

                # Find redaction after this
                if were_made_to and were_made_to[0] < next_x < were_made_to[0] + 1000:
                    print(f"  Next text: '{next_text}' at ({next_x}, )")

# Find ALL redactions and show them with context
print(f"\nAll redactions in the document:")
_, black_mask = cv2.threshold(gray, 5, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if 200 < w < 800:
        print(f"  Redaction at ({x}, {y}), size: {w}x{h}px")
