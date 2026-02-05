#!/usr/bin/env python3
"""Analyze redactions between 'with' and 'last'"""

import cv2
import numpy as np
from pdf2image import convert_from_path

FILE_PATH = "files/EFTA00037366.pdf"

# Load at 1200 DPI
images = convert_from_path(FILE_PATH, dpi=1200)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

# Area of interest: between "with" (4925) and "last" (5913), around y=2600
roi_x1, roi_y1 = 4800, 2500
roi_x2, roi_y2 = 6100, 2800

# Extract that region
region = gray[roi_y1:roi_y2, roi_x1:roi_x2].copy()

# Find redactions
_, black_mask = cv2.threshold(region, 5, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

print(f"Redactions between 'with' and 'last':")
for i, cnt in enumerate(contours):
    x, y, w, h = cv2.boundingRect(cnt)
    # Adjust to global coordinates
    global_x = x + roi_x1
    global_y = y + roi_y1

    if w > 100:
        print(f"  #{i+1}: at ({global_x}, {global_y}), size: {w}x{h}px")

# Save visualization
vis = cv2.cvtColor(region, cv2.COLOR_GRAY2BGR)

# Draw boxes
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if w > 100:
        cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.putText(vis, f"{w}px", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

cv2.imwrite("kellen_between_with_last.png", vis)
print(f"\nSaved: kellen_between_with_last.png")
