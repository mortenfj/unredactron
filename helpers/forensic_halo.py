#!/usr/bin/env python3
"""
Forensic Halo Extraction Module - Advanced Artifact Detection

This module implements sophisticated "Halo Extraction" for analyzing redaction edges:
1. Corner Exclusion - Removes noise from sharp corners
2. Side-Wall Separation - Isolates top/bottom/left/right edge zones
3. Forensic Enhancement - Contrast stretching, bit-plane slicing, ELA
4. Diagnostic Mode - Generates forensic sheets for manual analysis

Author: Unredactron Enhancement Module
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image, ImageFont, ImageDraw
import os
from typing import Tuple, List, Dict, Optional


class ForensicHaloExtractor:
    """Advanced halo extraction with corner exclusion and forensic enhancement."""

    def __init__(self, dpi: int = 600, halo_thickness: int = 6, corner_radius: int = 15):
        """
        Initialize the forensic halo extractor.

        Args:
            dpi: DPI for PDF conversion (higher = more detail)
            halo_thickness: Width of edge buffer zone in pixels
            corner_radius: Radius of corner exclusion zone
        """
        self.dpi = dpi
        self.halo_thickness = halo_thickness
        self.corner_radius = corner_radius

    def extract_halo_with_corner_exclusion(
        self,
        image: np.ndarray,
        redaction: Tuple[int, int, int, int]
    ) -> Dict[str, np.ndarray]:
        """
        Extract the halo region around a redaction with corner exclusion.

        Args:
            image: Grayscale image of the document
            redaction: (x, y, w, h) bounding box of redaction

        Returns:
            Dictionary with 'full', 'top', 'bottom', 'left', 'right' halo regions
        """
        x, y, w, h = redaction
        img_h, img_w = image.shape

        # Define extended region (redaction + halo buffer)
        pad = self.halo_thickness
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(img_w, x + w + pad)
        y2 = min(img_h, y + h + pad)

        # Extract extended ROI
        roi = image[y1:y2, x1:x2].copy()

        # Create masks for corner exclusion (diamond/circular shape)
        corner_mask = self._create_corner_exclusion_mask(roi.shape, w, h, pad)

        # Create mask for the redaction box itself (within ROI)
        box_mask = np.zeros_like(roi)
        box_x = x - x1
        box_y = y - y1
        box_mask[box_y:box_y+h, box_x:box_x+w] = 255

        # Combine: exclude redaction box AND corners
        halo_mask = cv2.bitwise_and(
            cv2.bitwise_not(box_mask),
            cv2.bitwise_not(corner_mask)
        )

        # Extract halo pixels
        halo_full = cv2.bitwise_and(roi, roi, mask=halo_mask)

        # Extract individual side walls
        sides = self._extract_side_walls(roi, box_x, box_y, w, h, pad, corner_mask)

        return {
            'full': halo_full,
            'mask': halo_mask,
            'roi': roi,
            'box_coords': (box_x, box_y, w, h),
            **sides
        }

    def _create_corner_exclusion_mask(
        self,
        shape: Tuple[int, int],
        box_w: int,
        box_h: int,
        pad: int
    ) -> np.ndarray:
        """
        Create a mask that zeros out the four corners of the extended region.

        Uses a diamond shape to smoothly exclude corner noise.
        """
        mask = np.zeros(shape[:2], dtype=np.uint8)

        # Get dimensions
        roi_h, roi_w = shape[:2]

        # Create diamond masks for each corner
        # The diamond extends into the corner by corner_radius
        r = self.corner_radius

        # Top-left corner
        for i in range(min(r, roi_h)):
            for j in range(min(r, roi_w)):
                if i + j < r:
                    mask[i, j] = 255

        # Top-right corner
        for i in range(min(r, roi_h)):
            for j in range(roi_w - min(r, roi_w), roi_w):
                if i + (roi_w - j - 1) < r:
                    mask[i, j] = 255

        # Bottom-left corner
        for i in range(roi_h - min(r, roi_h), roi_h):
            for j in range(min(r, roi_w)):
                if (roi_h - i - 1) + j < r:
                    mask[i, j] = 255

        # Bottom-right corner
        for i in range(roi_h - min(r, roi_h), roi_h):
            for j in range(roi_w - min(r, roi_w), roi_w):
                if (roi_h - i - 1) + (roi_w - j - 1) < r:
                    mask[i, j] = 255

        return mask

    def _extract_side_walls(
        self,
        roi: np.ndarray,
        box_x: int,
        box_y: int,
        box_w: int,
        box_h: int,
        pad: int,
        corner_mask: np.ndarray
    ) -> Dict[str, np.ndarray]:
        """
        Extract four separate slivers: top, bottom, left, right.

        These are the most valuable for identifying character shapes.
        """
        sides = {}

        # Top wall (above redaction, excluding corners)
        top = roi[box_y:box_y+pad, box_x:box_x+box_w].copy()
        top_corner_mask = corner_mask[box_y:box_y+pad, box_x:box_x+box_w]
        top = cv2.bitwise_and(top, top, mask=cv2.bitwise_not(top_corner_mask))
        sides['top'] = top

        # Bottom wall (below redaction, excluding corners)
        bottom = roi[box_y+box_h:box_y+box_h+pad, box_x:box_x+box_w].copy()
        bottom_corner_mask = corner_mask[box_y+box_h:box_y+box_h+pad, box_x:box_x+box_w]
        bottom = cv2.bitwise_and(bottom, bottom, mask=cv2.bitwise_not(bottom_corner_mask))
        sides['bottom'] = bottom

        # Left wall (left of redaction, excluding corners)
        left = roi[box_y:box_y+box_h, box_x:box_x+pad].copy()
        left_corner_mask = corner_mask[box_y:box_y+box_h, box_x:box_x+pad]
        left = cv2.bitwise_and(left, left, mask=cv2.bitwise_not(left_corner_mask))
        sides['left'] = left

        # Right wall (right of redaction, excluding corners)
        right = roi[box_y:box_y+box_h, box_x+box_w:box_x+box_w+pad].copy()
        right_corner_mask = corner_mask[box_y:box_y+box_h, box_x+box_w:box_x+box_w+pad]
        right = cv2.bitwise_and(right, right, mask=cv2.bitwise_not(right_corner_mask))
        sides['right'] = right

        return sides

    def apply_forensic_enhancement(self, halo: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Apply multiple forensic enhancement techniques to make artifacts visible.

        Returns:
            Dictionary with enhanced versions:
            - 'contrast': Extreme contrast stretching
            - 'edges': Canny edge detection
            - 'bitplane': Least significant bit plane
            - 'ela': Error Level Analysis
        """
        enhanced = {}

        # 1. Extreme Contrast Stretching
        # Amplify near-white pixels to make anti-aliasing visible
        stretched = cv2.normalize(halo, None, 0, 255, cv2.NORM_MINMAX)
        # Further stretch the high end
        enhanced['contrast'] = cv2.convertScaleAbs(stretched, alpha=3.0, beta=-200)

        # 2. Canny Edge Detection
        # Trace structural outlines of letter shapes
        enhanced['edges'] = cv2.Canny(halo, 30, 100)

        # 3. Bit-Plane Slicing
        # Extract least significant bits where subtle modifications often reside
        lsb = halo & 0x03  # Get 2 least significant bits
        enhanced['bitplane'] = (lsb * 85).astype(np.uint8)  # Scale to 0-255

        # 4. Error Level Analysis (ELA)
        # Detect compression artifacts that indicate multi-layer modification
        enhanced['ela'] = self._perform_ela(halo)

        return enhanced

    def _perform_ela(self, image: np.ndarray, quality: int = 90) -> np.ndarray:
        """
        Perform Error Level Analysis to detect compression inconsistencies.

        Saves the image at a known quality, reloads it, and calculates the difference.
        Regions with different compression levels indicate potential modification.
        """
        # Encode with specified quality
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        _, encoded = cv2.imencode('.jpg', image, encode_param)
        decoded = cv2.imdecode(encoded, cv2.IMREAD_GRAYSCALE)

        # Calculate difference
        ela = np.abs(image.astype(np.int16) - decoded.astype(np.int16))
        ela = np.clip(ela * 10, 0, 255).astype(np.uint8)  # Amplify differences

        return ela

    def analyze_halo_for_artifacts(
        self,
        halo_data: Dict[str, np.ndarray]
    ) -> Dict[str, any]:
        """
        Analyze extracted halo regions for artifact indicators.

        Returns quantitative metrics about detected artifacts.
        """
        results = {}

        # Analyze each side wall
        for side in ['top', 'bottom', 'left', 'right']:
            if side in halo_data:
                side_data = halo_data[side]

                # Skip if empty
                if side_data.size == 0:
                    results[f'{side}_artifact_score'] = 0.0
                    results[f'{side}_dark_pixels'] = 0
                    continue

                # Count dark pixels (potential letter traces)
                dark_pixels = np.sum(side_data < 150)
                total_pixels = side_data.size

                # Calculate artifact score
                results[f'{side}_dark_pixels'] = dark_pixels
                results[f'{side}_artifact_score'] = (dark_pixels / total_pixels * 100) if total_pixels > 0 else 0

        # Analyze edges
        if 'top' in halo_data and halo_data['top'].size > 0:
            top_edges = cv2.Canny(halo_data['top'], 30, 100)
            results['top_edge_count'] = np.sum(top_edges > 0)

        if 'bottom' in halo_data and halo_data['bottom'].size > 0:
            bottom_edges = cv2.Canny(halo_data['bottom'], 30, 100)
            results['bottom_edge_count'] = np.sum(bottom_edges > 0)

        return results

    def create_forensic_sheet(
        self,
        original: np.ndarray,
        halo_data: Dict[str, np.ndarray],
        enhanced: Dict[str, np.ndarray],
        redaction: Tuple[int, int, int, int],
        candidate_name: Optional[str] = None,
        output_path: str = "forensic_sheet.png"
    ) -> None:
        """
        Create a composite forensic sheet showing all enhancement views.

        The sheet includes:
        - Original redaction
        - Halo slivers (top, bottom, left, right)
        - Enhanced versions (contrast, edges, bitplane, ELA)
        - Optional candidate name overlay
        """
        # Create a large canvas
        sheet_h, sheet_w = 1200, 1800
        sheet = np.ones((sheet_h, sheet_w), dtype=np.uint8) * 255

        # Helper to add section labels
        def add_label(img, text, y_pos=20):
            cv2.putText(img, text, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX,
                       0.5, (128,), 1)

        # 1. Top-left: Original redaction (zoomed)
        x, y, w, h = redaction
        orig_view = original[y:y+h, x:x+w] if y+h <= original.shape[0] and x+w <= original.shape[1] else np.zeros((100, 100), dtype=np.uint8)
        orig_view = cv2.resize(orig_view, (400, 200))
        sheet[50:250, 50:450] = orig_view
        add_label(sheet, "ORIGINAL", 70)

        # 2. Top-middle: Full halo
        if 'full' in halo_data:
            halo_view = cv2.resize(halo_data['full'], (400, 200))
            sheet[50:250, 500:900] = halo_view
            add_label(sheet, "HALO (CORNERS EXCLUDED)", 70)

        # 3. Top-right: Contrast enhanced
        if 'contrast' in enhanced:
            contrast_view = cv2.resize(enhanced['contrast'], (400, 200))
            sheet[50:250, 950:1350] = contrast_view
            add_label(sheet, "CONTRAST STRETCHED", 70)

        # 4. Second row: Side walls
        y_base = 300
        for i, side in enumerate(['top', 'bottom', 'left', 'right']):
            if side in halo_data and halo_data[side].size > 0:
                side_img = halo_data[side]
                # Resize to fit
                side_img = cv2.resize(side_img, (350, 150))
                x_pos = 50 + (i % 2) * 400
                y_pos = y_base + (i // 2) * 200
                sheet[y_pos:y_pos+150, x_pos:x_pos+350] = side_img
                add_label(sheet, f"{side.upper()} WALL", y_pos + 20)

        # 5. Third row: Edge detection
        y_base = 650
        if 'edges' in enhanced:
            edges_view = cv2.resize(enhanced['edges'], (400, 200))
            sheet[y_base:y_base+200, 50:450] = edges_view
            add_label(sheet, "CANNY EDGES", y_base + 20)

        # 6. Bit-plane slicing
        if 'bitplane' in enhanced:
            bitplane_view = cv2.resize(enhanced['bitplane'], (400, 200))
            sheet[y_base:y_base+200, 500:900] = bitplane_view
            add_label(sheet, "BIT-PLANE (LSB)", y_base + 20)

        # 7. ELA
        if 'ela' in enhanced:
            ela_view = cv2.resize(enhanced['ela'], (400, 200))
            sheet[y_base:y_base+200, 950:1350] = ela_view
            add_label(sheet, "ERROR LEVEL ANALYSIS", y_base + 20)

        # 8. Add candidate name if provided
        if candidate_name:
            y_text = 900
            cv2.putText(sheet, f"CANDIDATE: {candidate_name}", (50, y_text),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,), 2)

        # Save
        cv2.imwrite(output_path, sheet)


def run_forensic_analysis(
    file_path: str,
    output_dir: str = "forensic_output",
    diagnostic_mode: bool = True
) -> List[Dict]:
    """
    Run complete forensic halo analysis on a PDF document.

    Args:
        file_path: Path to PDF file
        output_dir: Directory for output images
        diagnostic_mode: If True, generate forensic sheets

    Returns:
        List of analysis results for each redaction
    """
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 100)
    print("FORENSIC HALO ANALYSIS - Advanced Artifact Detection")
    print("=" * 100)

    # Initialize extractor
    extractor = ForensicHaloExtractor(dpi=600, halo_thickness=6, corner_radius=15)

    # Convert PDF to image
    print(f"\n[1] Converting PDF to {extractor.dpi} DPI image...")
    images = convert_from_path(file_path, dpi=extractor.dpi)
    img = np.array(images[0])
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    print(f"    Image size: {img.shape[1]}x{img.shape[0]}px")

    # Find redactions
    print(f"\n[2] Locating redaction boxes...")
    _, black_mask = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    redactions = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 200 and h > 100:  # Filter for name-sized redactions
            redactions.append((x, y, w, h))

    redactions.sort(key=lambda b: b[1])
    print(f"    Found {len(redactions)} target redactions")

    # Analyze each redaction
    results = []

    for i, (x, y, w, h) in enumerate(redactions):
        print(f"\n{'='*100}")
        print(f"Redaction #{i+1} at ({x}, {y}), size: {w}x{h}px")
        print(f"{'='*100}")

        # Extract halo with corner exclusion
        halo_data = extractor.extract_halo_with_corner_exclusion(gray, (x, y, w, h))

        # Apply forensic enhancements
        enhanced = extractor.apply_forensic_enhancement(halo_data['full'])

        # Analyze for artifacts
        artifact_metrics = extractor.analyze_halo_for_artifacts(halo_data)

        print(f"\nArtifact Metrics:")
        for side in ['top', 'bottom', 'left', 'right']:
            if f'{side}_dark_pixels' in artifact_metrics:
                dark_pix = artifact_metrics[f'{side}_dark_pixels']
                score = artifact_metrics[f'{side}_artifact_score']
                print(f"  {side.upper():5s}: {dark_pix:5d} dark pixels ({score:5.2f}%)")

        if 'top_edge_count' in artifact_metrics:
            print(f"  TOP EDGES:    {artifact_metrics['top_edge_count']} edge pixels")
        if 'bottom_edge_count' in artifact_metrics:
            print(f"  BOTTOM EDGES: {artifact_metrics['bottom_edge_count']} edge pixels")

        # Calculate overall artifact confidence
        artifact_confidence = (
            artifact_metrics.get('top_artifact_score', 0) * 0.3 +
            artifact_metrics.get('bottom_artifact_score', 0) * 0.3 +
            artifact_metrics.get('left_artifact_score', 0) * 0.2 +
            artifact_metrics.get('right_artifact_score', 0) * 0.2
        )

        result = {
            'index': i,
            'coords': (x, y, w, h),
            'artifact_metrics': artifact_metrics,
            'artifact_confidence': artifact_confidence,
            'has_artifacts': artifact_confidence > 1.0
        }
        results.append(result)

        # Generate diagnostic sheet if enabled
        if diagnostic_mode and result['has_artifacts']:
            output_path = f"{output_dir}/forensic_{i:03d}_x{x}_y{y}.png"
            extractor.create_forensic_sheet(
                gray,
                halo_data,
                enhanced,
                (x, y, w, h),
                output_path=output_path
            )
            print(f"\n  ✓ Forensic sheet saved: {output_path}")

    # Summary
    print(f"\n{'='*100}")
    print(f"ANALYSIS COMPLETE")
    print(f"{'='*100}")

    with_artifacts = sum(1 for r in results if r['has_artifacts'])
    print(f"\nRedactions with detected artifacts: {with_artifacts}/{len(results)}")

    if with_artifacts > 0:
        print(f"\nRedactions showing artifact signals:")
        for r in results:
            if r['has_artifacts']:
                conf = r['artifact_confidence']
                coords = r['coords']
                print(f"  #{r['index']+1} at ({coords[0]}, {coords[1]}): {conf:.2f}% confidence")

    print(f"\nForensic sheets saved to: {output_dir}/")

    return results


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "files/EFTA00037366.pdf"

    run_forensic_analysis(pdf_path, diagnostic_mode=True)
