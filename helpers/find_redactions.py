#!/usr/bin/env python3
"""
Scan all pages of the PDF to find redaction blocks.
"""

import cv2
import numpy as np
from pdf2image import convert_from_path

FILE_PATH = "files/EFTA00513855.pdf"

def find_redactions(image_cv):
    """Locates black bars using Computer Vision contours."""
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    redactions = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 30 and h > 10 and w/h > 1.5:
            redactions.append((x, y, w, h))

    redactions.sort(key=lambda b: b[1])
    return redactions

print(f"Loading {FILE_PATH}...")
pages = convert_from_path(FILE_PATH)
print(f"Loaded {len(pages)} pages\n")

pages_with_redactions = []

for i, page in enumerate(pages):
    img = np.array(page)
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    redactions = find_redactions(img_bgr)

    if redactions:
        pages_with_redactions.append((i+1, redactions))
        print(f"Page {i+1:2d}: {len(redactions)} redaction(s) found")
        for j, (x, y, w, h) in enumerate(redactions):
            print(f"         Block {j+1}: pos=({x:4d},{y:4d}), size={w:3d}x{h:3d}px")
    else:
        print(f"Page {i+1:2d}: No redactions")

print(f"\n{'='*60}")
print(f"Summary: {len(pages_with_redactions)} pages have redactions")
print(f"{'='*60}")

if pages_with_redactions:
    print("\nRecommended pages to analyze:")
    for page_num, redactions in pages_with_redactions:
        print(f"  - Page {page_num} ({len(redactions)} redaction blocks)")
