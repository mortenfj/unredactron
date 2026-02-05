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
from typing import Tuple, Optional, Dict


def detect_best_font(
    pdf_path: str,
    fonts_dir: str = "fonts/fonts/",
    min_confidence: int = 85,
    min_text_length: int = 4,
    max_text_length: int = 20,
    min_width: int = 30,
    size_range: Tuple[int, int] = (8, 19),
    min_measurements: int = 5,
    verbose: bool = False
) -> Optional[Dict]:
    """
    Detect the best matching font from a PDF document by analyzing visible text.

    Args:
        pdf_path: Path to the PDF file
        fonts_dir: Directory containing font files
        min_confidence: Minimum OCR confidence for text samples
        min_text_length: Minimum text length to use for calibration
        max_text_length: Maximum text length to use for calibration
        min_width: Minimum pixel width for text samples
        size_range: Tuple of (min_size, max_size) for font size testing
        min_measurements: Minimum number of measurements required
        verbose: Print detailed progress

    Returns:
        Dictionary with:
            - font_path: Full path to font file
            - font_name: Font file name
            - font_size: Detected font size in points
            - scale_factor: Calculated scale factor
            - std_dev: Standard deviation of measurements
            - consistency: Coefficient of variation percentage
        Or None if detection fails
    """
    # Load document
    try:
        pages = convert_from_path(pdf_path)
    except Exception as e:
        if verbose:
            print(f"[ERROR] Failed to load PDF: {e}")
        return None

    img = np.array(pages[0])
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    if verbose:
        print(f"[*] Document: {pdf_path}")
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
        if conf > min_confidence and min_text_length <= len(text) <= max_text_length and w > min_width:
            visible_text.append((text, w, conf))

    if len(visible_text) < min_measurements:
        if verbose:
            print(f"[ERROR] Not enough high-confidence text samples ({len(visible_text)} < {min_measurements})")
        return None

    if verbose:
        print(f"[*] Found {len(visible_text)} high-confidence visible text samples")

    # Test each font
    font_files = sorted([f for f in os.listdir(fonts_dir) if f.endswith('.ttf') or f.endswith('.TTF')])

    if verbose:
        print(f"[*] Testing {len(font_files)} fonts against visible text...")

    results = []

    for font_file in font_files:
        font_path = os.path.join(fonts_dir, font_file)

        # Test different font sizes
        for font_size in range(size_range[0], size_range[1], 1):
            try:
                font = ImageFont.truetype(font_path, font_size)

                # Calculate scale factors from multiple words
                scale_factors = []

                for text, actual_width, conf in visible_text:
                    try:
                        theoretical_width = font.getlength(text)
                        if theoretical_width > 0:
                            sf = actual_width / theoretical_width
                            scale_factors.append(sf)
                    except:
                        pass

                if len(scale_factors) < min_measurements:
                    continue  # Need at least minimum measurements

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

    if not results:
        if verbose:
            print("[ERROR] No suitable font found")
        return None

    best = results[0]

    if verbose:
        print(f"\n[*] DETECTED FONT: {best['font']} at {best['size']}pt")
        print(f"    Scale Factor:      {best['avg_scale']:.4f}")
        print(f"    Standard Deviation: {best['std_dev']:.4f}")
        print(f"    Consistency:       {best['consistency']:.2f}% (lower = better)")
        print(f"    Measurements:      {best['num_measurements']} text samples")

    return {
        'font_path': os.path.join(fonts_dir, best['font']),
        'font_name': best['font'],
        'font_size': best['size'],
        'scale_factor': best['avg_scale'],
        'std_dev': best['std_dev'],
        'consistency': best['consistency'],
        'num_measurements': best['num_measurements']
    }


if __name__ == "__main__":
    FILE_PATH = "files/EFTA00037366.pdf"
    FONTS_DIR = "fonts/fonts/"

    print("="*100)
    print("FONT DETECTION BY ANALYZING VISIBLE TEXT")
    print("="*100)

    result = detect_best_font(FILE_PATH, FONTS_DIR, verbose=True)

    if result:
        print(f"\n{'='*100}")
        print("RECOMMENDATION")
        print("="*100)
        print(f"Update main.py with:")
        print(f"  FONT_PATH = '{result['font_path']}'")
        print(f"  font_size_pt = {result['font_size']}")
        print(f"  (This will automatically set scale factor to {result['scale_factor']:.4f})")
    else:
        print("\n[ERROR] Font detection failed")
