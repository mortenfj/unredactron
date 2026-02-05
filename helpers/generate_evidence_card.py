#!/usr/bin/env python3
"""
Forensic Evidence Card Generator

Creates a composite image summarizing why a specific candidate is a match
for a specific redaction. This is for presentation to stakeholders.

Usage:
    python generate_evidence_card.py --pdf files/document.pdf --redaction-index 4 \
        --candidate-name "Jean-Luc" --highlight-pos 6

Author: Unredactron Forensic Module
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import ImageFont, Image, ImageDraw
import argparse
import os
import sys
from typing import Tuple, List, Optional, Dict

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from helpers.label_utils import add_safe_header_legacy
from helpers.forensic_halo import ForensicHaloExtractor
from font_profiler import FontProfiler


class EvidenceCardGenerator:
    """Generates forensic evidence cards for redaction matches."""

    def __init__(self, dpi: int = 600, font_path: str = "fonts/fonts/times.ttf"):
        """
        Initialize the evidence card generator.

        Args:
            dpi: DPI for PDF conversion
            font_path: Path to font file for rendering candidate names
        """
        self.dpi = dpi
        self.font_path = font_path
        self.font = ImageFont.truetype(font_path, 12)
        self.halo_extractor = ForensicHaloExtractor(dpi=dpi)

    def load_pdf(self, pdf_path: str, page: int = 0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load PDF and convert to image.

        Args:
            pdf_path: Path to PDF file
            page: Page number (0-indexed)

        Returns:
            Tuple of (color_image, grayscale_image)
        """
        print(f"[*] Loading PDF: {pdf_path}")
        images = convert_from_path(pdf_path, dpi=self.dpi)

        if page >= len(images):
            raise ValueError(f"Page {page} not found (document has {len(images)} pages)")

        img = np.array(images[page])
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        print(f"    Image size: {img.shape[1]}x{img.shape[0]}px at {self.dpi} DPI")
        return img, gray

    def find_redactions(self, gray: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Find all redaction boxes in the image.

        Args:
            gray: Grayscale image

        Returns:
            List of (x, y, w, h) bounding boxes
        """
        _, black_mask = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        redactions = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 200 and h > 100:  # Filter for name-sized redactions
                redactions.append((x, y, w, h))

        redactions.sort(key=lambda b: b[1])
        print(f"    Found {len(redactions)} target redactions")
        return redactions

    def get_font_profile(self, gray: np.ndarray) -> Optional[Dict]:
        """
        Auto-detect font profile from the document.

        Args:
            gray: Grayscale image

        Returns:
            Dictionary with font parameters or None
        """
        print(f"[*] Auto-detecting font profile...")
        profiler = FontProfiler(fonts_dir="fonts/fonts/")

        # Convert back to color for OCR
        img_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        profile = profiler.profile_document(img_bgr, dpi=self.dpi, verbose=False)

        if profile:
            print(f"    Detected: {profile.font_name} {profile.font_size:.1f}pt "
                  f"(scale: {profile.scale_factor:.4f})")
            self.font = ImageFont.truetype(profile.font_path, int(profile.font_size))
            return {
                'font_path': profile.font_path,
                'font_size': profile.font_size,
                'scale_factor': profile.scale_factor,
                'tracking_offset': profile.tracking_offset
            }
        else:
            print(f"    Using default font: {self.font_path}")
            return {'scale_factor': self.dpi / 72, 'tracking_offset': 0}

    def create_panel1_geometric_fit(
        self,
        img: np.ndarray,
        redaction: Tuple[int, int, int, int],
        candidate_name: str,
        font_profile: Dict
    ) -> np.ndarray:
        """
        Create Panel 1: Geometric Fit - X-Ray View with split overlay.

        Shows three layers:
        - Top: Original Redaction
        - Middle: 50% Opacity Overlay (name inside redaction box)
        - Bottom: Candidate Name rendered in black text
        - Green vertical guidelines cutting through all layers

        Args:
            img: Original image
            redaction: (x, y, w, h) of redaction box
            candidate_name: Name to render
            font_profile: Font parameters

        Returns:
            Panel image with header
        """
        x, y, w, h = redaction

        # Extract redaction box
        redaction_crop = img[y:y+h, x:x+w].copy()

        # Render the candidate name
        scale_factor = font_profile['scale_factor']
        tracking_offset = font_profile.get('tracking_offset', 0)

        # Calculate expected width
        base_width = self.font.getlength(candidate_name)
        expected_width = base_width * scale_factor + (len(candidate_name) * tracking_offset)

        # Create the three-layer split view
        # Each layer has same width (max of redaction and text width)
        layer_w = max(w, int(expected_width) + 20)
        layer_h = h

        # Layer 1 (Top): Original Redaction
        layer1 = np.ones((layer_h, layer_w, 3), dtype=np.uint8) * 255
        redaction_x = (layer_w - w) // 2
        layer1[:, redaction_x:redaction_x+w] = redaction_crop

        # Layer 2 (Middle): 50% Opacity Overlay
        layer2 = redaction_crop.copy()
        img_pil = Image.fromarray(layer2)
        draw = ImageDraw.Draw(img_pil, 'RGBA')

        # Render white text at 50% opacity (128/255)
        text_x = (w - int(expected_width)) // 2
        text_y = (h - int(font_profile.get('font_size', 12) * scale_factor)) // 2
        draw.text((text_x, text_y), candidate_name, font=self.font, fill=(255, 255, 255, 128))

        # Convert back and ensure dimensions match exactly
        layer2_rendered = np.array(img_pil)

        # Center layer2 in the layer width, ensuring exact dimensions
        layer2_centered = np.ones((layer_h, layer_w, 3), dtype=np.uint8) * 255
        layer2_x = (layer_w - layer2_rendered.shape[1]) // 2
        # Copy with safe bounds
        h2_copy = min(layer2_rendered.shape[0], layer_h)
        w2_copy = min(layer2_rendered.shape[1], layer_w - layer2_x)
        layer2_centered[:h2_copy, layer2_x:layer2_x+w2_copy] = layer2_rendered[:h2_copy, :w2_copy]

        # Layer 3 (Bottom): Candidate Name in Black Text
        # Create a temporary canvas for text rendering
        layer3_temp = np.ones((layer_h, layer_w, 3), dtype=np.uint8) * 255
        img_pil3 = Image.fromarray(layer3_temp)
        draw3 = ImageDraw.Draw(img_pil3)
        text_x3 = (layer_w - int(expected_width)) // 2
        text_y3 = (layer_h - int(font_profile.get('font_size', 12) * scale_factor)) // 2
        draw3.text((text_x3, text_y3), candidate_name, font=self.font, fill=(0, 0, 0))

        # Convert back and ensure dimensions match exactly
        layer3_rendered = np.array(img_pil3)
        # Create the final layer3 with exact dimensions
        layer3 = np.ones((layer_h, layer_w, 3), dtype=np.uint8) * 255
        # Copy the rendered content, handling any size mismatch
        h_copy = min(layer3_rendered.shape[0], layer_h)
        w_copy = min(layer3_rendered.shape[1], layer_w)
        layer3[:h_copy, :w_copy] = layer3_rendered[:h_copy, :w_copy]

        # Stack layers vertically with spacing
        spacing = 15
        header_reserve = 50  # Reserve space for header that will be added later
        panel_h = layer_h * 3 + spacing * 2 + header_reserve
        panel_w = layer_w + 40

        panel = np.ones((panel_h, panel_w, 3), dtype=np.uint8) * 255

        # Position layers (start below the reserved header space)
        layer1_x = (panel_w - layer1.shape[1]) // 2
        layer1_y = header_reserve  # Start below the header
        panel[layer1_y:layer1_y+layer_h, layer1_x:layer1_x+layer_w] = layer1

        layer2_y = layer1_y + layer_h + spacing
        panel[layer2_y:layer2_y+layer_h, layer1_x:layer1_x+layer_w] = layer2_centered

        layer3_y = layer2_y + layer_h + spacing
        panel[layer3_y:layer3_y+layer_h, layer1_x:layer1_x+layer_w] = layer3

        # Draw distinct Green Guidelines cutting through all layers
        # These show the start and end of the redaction box
        green = (0, 200, 0)
        guideline_left = layer1_x + redaction_x
        guideline_right = layer1_x + redaction_x + w

        # Left guideline (cuts through all three layers)
        cv2.line(panel, (guideline_left, layer1_y),
                 (guideline_left, layer3_y + layer_h), green, 2)

        # Right guideline (cuts through all three layers)
        cv2.line(panel, (guideline_right, layer1_y),
                 (guideline_right, layer3_y + layer_h), green, 2)

        # Add labels for each layer
        label_y_offset = 5
        cv2.putText(panel, "ORIGINAL", (10, layer1_y + 20),
                   cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 0, 0), 1)
        cv2.putText(panel, "50% OVERLAY", (10, layer2_y + 20),
                   cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 0, 0), 1)
        cv2.putText(panel, "CANDIDATE", (10, layer3_y + 20),
                   cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 0, 0), 1)

        # Add header text to the reserved space at the top
        cv2.putText(panel, "EVIDENCE 1: GEOMETRIC FIT (X-Ray Width Match)",
                    (10, 35), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 0, 0), 2)

        return panel

    def create_panel2_contextual_fit(
        self,
        img: np.ndarray,
        gray: np.ndarray,
        redaction: Tuple[int, int, int, int],
        candidate_name: str,
        font_profile: Dict
    ) -> np.ndarray:
        """
        Create Panel 2: Contextual Fit - Fill-in-the-Blank View.

        Shows the name "restored" to the document with high-visibility text
        that pops against the black redaction bar.

        Args:
            img: Original color image
            gray: Grayscale image (for OCR)
            redaction: (x, y, w, h) of redaction box
            candidate_name: Name to overlay
            font_profile: Font parameters

        Returns:
            Panel image with header
        """
        x, y, w, h = redaction

        # Extract wider context (roughly 3-4 words on each side)
        context_width = int(w * 3)  # Wider crop
        context_x = max(0, x - context_width // 2)
        context_y = max(0, y - 20)
        context_w = min(gray.shape[1] - context_x, context_width)
        context_h = min(gray.shape[0] - context_y, h + 40)

        context_crop = img[context_y:context_y+context_h, context_x:context_x+context_w].copy()

        # Create semi-transparent overlay
        overlay = context_crop.copy()

        # Render the candidate name for overlay
        scale_factor = font_profile['scale_factor']
        tracking_offset = font_profile.get('tracking_offset', 0)
        expected_width = self.font.getlength(candidate_name) * scale_factor + (len(candidate_name) * tracking_offset)

        # Calculate position within context crop
        name_x = x - context_x + (w - int(expected_width)) // 2
        name_y = y - context_y + (h - 20) // 2

        # Draw semi-transparent text with HIGH VISIBILITY
        # Changed from black (0,0,0,180) to bright white (255,255,255,220)
        img_pil = Image.fromarray(overlay)
        draw = ImageDraw.Draw(img_pil, 'RGBA')

        # Create bright white text at 220 opacity (almost solid)
        # This "fills" the black void with visible text
        draw.text((name_x, name_y), candidate_name,
                 font=self.font, fill=(255, 255, 255, 220))

        overlay_with_text = np.array(img_pil)

        # Blend original with overlay (50% opacity)
        blended = cv2.addWeighted(context_crop, 0.5, overlay_with_text, 0.5, 0)

        # Draw red rectangle around the redaction area
        rel_x = x - context_x
        rel_y = y - context_y
        cv2.rectangle(blended, (rel_x, rel_y), (rel_x + w, rel_y + h), (0, 0, 255), 2)

        # Add header
        header_height = 50
        panel_with_header = cv2.copyMakeBorder(
            blended, header_height, 0, 0, 0,
            cv2.BORDER_CONSTANT, value=(255, 255, 255)
        )
        cv2.putText(panel_with_header, "EVIDENCE 2: CONTEXTUAL FIT (Name Restored to Document)",
                    (10, 35), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 0, 0), 2)

        return panel_with_header

    def create_panel3_artifact_fingerprint(
        self,
        gray: np.ndarray,
        redaction: Tuple[int, int, int, int],
        candidate_name: str,
        font_profile: Dict,
        highlight_pos: Optional[int] = None
    ) -> np.ndarray:
        """
        Create Panel 3: Artifact Fingerprint - Letter Outline Overlay.

        Shows the candidate name as a wireframe/outline overlaid directly on the
        enhanced artifact halo, allowing visual alignment of letter shapes with
        artifact pixels.

        Args:
            gray: Grayscale image
            redaction: (x, y, w, h) of redaction box
            candidate_name: Candidate name to render as outline
            font_profile: Font parameters for rendering
            highlight_pos: Optional position to highlight with magnifying glass

        Returns:
            Panel image with header and optional magnifying glass annotation
        """
        x, y, w, h = redaction

        # Extract halo data with corner exclusion
        halo_data = self.halo_extractor.extract_halo_with_corner_exclusion(gray, redaction)
        top_wall = halo_data['top']

        # Apply forensic enhancement to top wall (contrast stretching)
        enhanced_top = self.halo_extractor.apply_forensic_enhancement(top_wall)
        contrast_view = enhanced_top['contrast']

        # Panel dimensions
        panel_h = 250
        panel_w = 500
        padding = 40

        # Create panel with the enhanced halo as the background
        panel = np.ones((panel_h, panel_w, 3), dtype=np.uint8) * 255

        # Resize and place the halo view at the top of the panel
        halo_display_h = 180
        halo_display_w = panel_w - 2 * padding
        halo_resized = cv2.resize(contrast_view, (halo_display_w, halo_display_h))

        # Convert to color and place
        halo_x = padding
        halo_y = 60  # Leave room for labels
        halo_color = cv2.cvtColor(halo_resized, cv2.COLOR_GRAY2BGR)
        panel[halo_y:halo_y+halo_display_h, halo_x:halo_x+halo_display_w] = halo_color

        # Calculate scaling from original top_wall to display
        scale_x = halo_display_w / top_wall.shape[1]

        # Render the candidate name as a wireframe/outline
        # Use cyan (255, 255, 0) or red (0, 0, 255) for high contrast
        outline_color = (255, 255, 0)  # Cyan in BGR

        # Calculate text position and scale
        scale_factor = font_profile['scale_factor']
        tracking_offset = font_profile.get('tracking_offset', 0)
        expected_width = self.font.getlength(candidate_name) * scale_factor + (len(candidate_name) * tracking_offset)

        # Scale expected width to match the halo display width
        # The halo display width should match the redaction width
        redaction_display_width = w * scale_x
        text_display_width = expected_width * scale_x

        # Calculate text position (centered in the halo area)
        text_x = halo_x + (halo_display_w - int(text_display_width)) // 2

        # Get font size and calculate vertical position
        font_size = font_profile.get('font_size', 12)
        font_scale_size = int(font_size * scale_factor * scale_x)
        text_y = halo_y + (halo_display_h - font_scale_size) // 2

        # Create a mask for the text outline
        # We'll render the text and find its edges
        temp_canvas = np.zeros((halo_display_h, halo_display_w, 3), dtype=np.uint8)
        temp_pil = Image.fromarray(temp_canvas)
        temp_draw = ImageDraw.Draw(temp_pil)

        # Use a scaled font for the display
        scaled_font_size = max(int(font_size * scale_factor * scale_x * 0.8), 10)
        scaled_font = ImageFont.truetype(font_profile.get('font_path', self.font_path), scaled_font_size)

        # Render white text on black background
        temp_draw.text((10, halo_display_h // 2 - scaled_font_size // 2), candidate_name,
                      font=scaled_font, fill=(255, 255, 255))
        temp_mask = np.array(temp_pil)

        # Convert to grayscale and find edges using Canny
        temp_gray = cv2.cvtColor(temp_mask, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(temp_gray, 100, 200)

        # Find contours of the text (this gives us the wireframe)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        # Draw the contours on the panel in cyan
        for contour in contours:
            # Scale and position the contour correctly
            adjusted_contour = contour.copy()
            adjusted_contour[:, 0, 0] = adjusted_contour[:, 0, 0] + text_x - 10
            adjusted_contour[:, 0, 1] = adjusted_contour[:, 0, 1] + text_y - (halo_display_h // 2 - scaled_font_size // 2)
            cv2.drawContours(panel, [adjusted_contour], -1, outline_color, 1)

        # Add label at the top
        cv2.putText(panel, "Enhanced Artifacts + Letter Outline",
                    (padding, 30), cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 0, 0), 1)

        # AUTOMATIC ARTIFACT DETECTION (for console output)
        num_chars = len(candidate_name)
        artifact_scores = []

        for i in range(num_chars):
            # Calculate corresponding region in the original top wall
            slot_start_x = int((i / num_chars) * top_wall.shape[1])
            slot_end_x = int(((i + 1) / num_chars) * top_wall.shape[1])

            # Extract this slot from the top wall
            slot_region = top_wall[:, slot_start_x:slot_end_x]

            # Count dark pixels (artifacts)
            dark_pixels = np.sum(slot_region < 150)
            total_pixels = slot_region.size
            artifact_score = (dark_pixels / total_pixels * 100) if total_pixels > 0 else 0

            artifact_scores.append({
                'position': i,
                'char': candidate_name[i] if i < len(candidate_name) else "?",
                'dark_pixels': dark_pixels,
                'artifact_score': artifact_score
            })

        # Print artifact detection results to console
        print(f"\n[*] ARTIFACT DETECTION RESULTS (Top Wall Analysis):")
        print(f"    Position  Character  Dark Pixels  Artifact %")
        print(f"    ---------  ---------  -----------  ----------")
        for score in artifact_scores:
            indicator = "⚠ ARTIFACTS" if score['artifact_score'] > 2.0 else "  clean"
            print(f"    {score['position']:2d}        {score['char']:^8s}  {score['dark_pixels']:5d}       "
                  f"{score['artifact_score']:5.1f}%    {indicator}")

        # Add magnifying glass annotation if highlight_pos is specified
        if highlight_pos is not None and 0 <= highlight_pos < num_chars:
            # Calculate position of the highlighted character
            char_start_x = int((highlight_pos / num_chars) * halo_display_w)
            char_end_x = int(((highlight_pos + 1) / num_chars) * halo_display_w)
            char_center_x = halo_x + (char_start_x + char_end_x) // 2
            char_center_y = halo_y + halo_display_h // 2

            # Draw magnifying glass circle
            magnifier_radius = 40
            cv2.circle(panel, (char_center_x, char_center_y), magnifier_radius,
                      (0, 0, 255), 3)

            # Add "handle" to magnifying glass
            handle_start = (char_center_x + int(magnifier_radius * 0.707),
                           char_center_y + int(magnifier_radius * 0.707))
            handle_end = (char_center_x + int(magnifier_radius * 1.2),
                         char_center_y + int(magnifier_radius * 1.2))
            cv2.line(panel, handle_start, handle_end, (0, 0, 255), 4)

            # Add annotation text
            char = candidate_name[highlight_pos]
            artifact_pct = artifact_scores[highlight_pos]['artifact_score']
            has_artifacts = artifact_pct > 2.0

            annotation_text = f"'{char}' position: "
            if has_artifacts:
                annotation_text += f"ARTIFACTS DETECTED ({artifact_pct:.1f}%)"
            else:
                annotation_text += f"Clean ({artifact_pct:.1f}%)"

            # Add text label
            label_y = halo_y + halo_display_h + 15
            cv2.putText(panel, annotation_text,
                       (padding, label_y), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 0, 255), 1)

            # Draw arrow from annotation to magnifier
            arrow_start = (padding + 200, label_y - 5)
            arrow_end = (char_center_x, char_center_y - magnifier_radius - 5)
            cv2.arrowedLine(panel, arrow_start, arrow_end, (0, 0, 255), 2)

        # Add header
        header_height = 50
        panel_with_header = cv2.copyMakeBorder(
            panel, header_height, 0, 0, 0,
            cv2.BORDER_CONSTANT, value=(255, 255, 255)
        )
        cv2.putText(panel_with_header,
                    "EVIDENCE 3: ARTIFACT FINGERPRINT (Letter outlines align with noise pixels)",
                    (10, 35), cv2.FONT_HERSHEY_DUPLEX, 0.65, (0, 0, 0), 2)

        return panel_with_header

    def create_evidence_card(
        self,
        pdf_path: str,
        redaction_index: int,
        candidate_name: str,
        highlight_pos: Optional[int] = None,
        output_dir: str = "evidence_cards"
    ) -> str:
        """
        Create the complete evidence card for a redaction match.

        Args:
            pdf_path: Path to PDF file
            redaction_index: Index of redaction (0-based)
            candidate_name: Candidate name to visualize
            highlight_pos: Optional position to highlight in artifacts
            output_dir: Output directory for evidence cards

        Returns:
            Path to saved evidence card image
        """
        print("=" * 100)
        print(f"FORENSIC MATCH EVIDENCE CARD GENERATOR")
        print("=" * 100)
        print(f"\n[*] Target: {candidate_name} (Redaction #{redaction_index})")
        if highlight_pos is not None:
            print(f"[*] Highlighting position: {highlight_pos}")

        # Load PDF
        img, gray = self.load_pdf(pdf_path)

        # Get font profile
        font_profile = self.get_font_profile(gray)

        # Find redactions
        redactions = self.find_redactions(gray)

        if redaction_index >= len(redactions):
            raise ValueError(f"Redaction index {redaction_index} not found "
                           f"(only {len(redactions)} redactions detected)")

        redaction = redactions[redaction_index]
        x, y, w, h = redaction
        print(f"\n[*] Target Redaction: #{redaction_index}")
        print(f"    Location: ({x}, {y}), Size: {w}x{h}px")

        # Create the three panels
        print(f"\n[*] Generating Panel 1: Geometric Fit...")
        panel1 = self.create_panel1_geometric_fit(img, redaction, candidate_name, font_profile)

        print(f"[*] Generating Panel 2: Contextual Fit...")
        panel2 = self.create_panel2_contextual_fit(img, gray, redaction, candidate_name, font_profile)

        print(f"[*] Generating Panel 3: Artifact Fingerprint...")
        panel3 = self.create_panel3_artifact_fingerprint(gray, redaction, candidate_name, font_profile, highlight_pos)

        # Create main title header
        title_text = f"FORENSIC MATCH EVIDENCE: {candidate_name.upper()} (REDACTION #{redaction_index})"

        # Calculate dimensions for composite
        gutter_size = 30  # White space between panels

        # Resize panels to match height (use max height)
        max_height = max(panel1.shape[0], panel2.shape[0], panel3.shape[0])

        # Resize panels to same height
        panel1 = cv2.resize(panel1, (panel1.shape[1], max_height))
        panel2 = cv2.resize(panel2, (panel2.shape[1], max_height))
        panel3 = cv2.resize(panel3, (panel3.shape[1], max_height))

        # Calculate total width
        total_width = panel1.shape[1] + panel2.shape[1] + panel3.shape[1] + (2 * gutter_size)

        # Create main title header
        header_height = 70
        composite = np.ones((header_height + max_height, total_width, 3), dtype=np.uint8) * 255

        # Draw title
        cv2.putText(composite, title_text,
                    (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)

        # Add panels with gutters
        x_offset = 0
        for panel in [panel1, panel2, panel3]:
            composite[header_height:, x_offset:x_offset+panel.shape[1]] = panel
            x_offset += panel.shape[1] + gutter_size

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Save evidence card
        safe_name = candidate_name.replace(" ", "_").replace("-", "_").lower()
        output_path = f"{output_dir}/match_{safe_name}_{redaction_index:03d}.png"
        cv2.imwrite(output_path, composite)

        print(f"\n[*] Evidence card saved: {output_path}")
        print(f"    Size: {composite.shape[1]}x{composite.shape[0]}px")

        return output_path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate forensic evidence cards for redaction matches'
    )
    parser.add_argument('--pdf', type=str, required=True,
                        help='Path to PDF file')
    parser.add_argument('--redaction-index', type=int, required=True,
                        help='Index of redaction (0-based)')
    parser.add_argument('--candidate-name', type=str, required=True,
                        help='Candidate name to visualize')
    parser.add_argument('--highlight-pos', type=int, default=None,
                        help='Position to highlight in artifact map (e.g., 6 for L in Jean-Luc)')
    parser.add_argument('--output-dir', type=str, default='evidence_cards',
                        help='Output directory for evidence cards')
    parser.add_argument('--dpi', type=int, default=600,
                        help='DPI for PDF conversion')
    parser.add_argument('--font', type=str, default='fonts/fonts/times.ttf',
                        help='Path to font file')

    args = parser.parse_args()

    # Create generator
    generator = EvidenceCardGenerator(dpi=args.dpi, font_path=args.font)

    # Generate evidence card
    try:
        output_path = generator.create_evidence_card(
            pdf_path=args.pdf,
            redaction_index=args.redaction_index,
            candidate_name=args.candidate_name,
            highlight_pos=args.highlight_pos,
            output_dir=args.output_dir
        )
        print(f"\n✓ Evidence card successfully generated!")
        print(f"  Output: {output_path}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
