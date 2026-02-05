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
        Create Panel 1: Geometric Fit - Shows width alignment.

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

        # Create a canvas for the rendered name
        text_canvas_h = h + 40
        text_canvas_w = max(w, int(expected_width) + 40)

        # Create white background for text
        text_canvas = np.ones((text_canvas_h, text_canvas_w, 3), dtype=np.uint8) * 255

        # Draw the text
        img_pil = Image.fromarray(text_canvas)
        draw = ImageDraw.Draw(img_pil)

        # Calculate text position (centered)
        text_y = 20
        text_x = (text_canvas_w - int(expected_width)) // 2

        draw.text((text_x, text_y), candidate_name, font=self.font, fill=(0, 0, 0))

        rendered_text = np.array(img_pil)

        # Create the panel with redaction above, text below
        panel_w = max(redaction_crop.shape[1], rendered_text.shape[1]) + 40
        panel_h = redaction_crop.shape[0] + rendered_text.shape[0] + 60

        panel = np.ones((panel_h, panel_w, 3), dtype=np.uint8) * 255

        # Center the redaction crop
        redaction_x = (panel_w - redaction_crop.shape[1]) // 2
        panel[20:20+h, redaction_x:redaction_x+w] = redaction_crop

        # Center the rendered text below
        text_y_offset = 20 + h + 20
        text_x_offset = (panel_w - rendered_text.shape[1]) // 2
        panel[text_y_offset:text_y_offset+rendered_text.shape[0],
              text_x_offset:text_x_offset+rendered_text.shape[1]] = rendered_text

        # Draw vertical red dashed lines showing alignment
        left_redaction_x = redaction_x
        right_redaction_x = redaction_x + w
        left_text_x = text_x_offset + text_x
        right_text_x = text_x_offset + text_x + int(expected_width)

        # Draw lines connecting the edges
        # Left edge line (from redaction bottom to text top)
        cv2.line(panel, (left_redaction_x + 2, 20 + h),
                 (left_text_x, text_y_offset + rendered_text.shape[0] // 2),
                 (0, 0, 255), 2)

        # Right edge line
        cv2.line(panel, (right_redaction_x - 2, 20 + h),
                 (right_text_x, text_y_offset + rendered_text.shape[0] // 2),
                 (0, 0, 255), 2)

        # Add red dashed circle at connection points
        cv2.circle(panel, (left_redaction_x + 2, 20 + h), 5, (0, 0, 255), 2)
        cv2.circle(panel, (right_redaction_x - 2, 20 + h), 5, (0, 0, 255), 2)

        # Convert to grayscale for header
        panel_gray = cv2.cvtColor(panel, cv2.COLOR_BGR2GRAY)

        # Add header
        panel_with_header = add_safe_header_legacy(
            panel_gray,
            "EVIDENCE 1: GEOMETRIC FIT (Width Match)",
            header_height=50
        )

        # Convert back to color
        panel_color = cv2.cvtColor(panel_with_header, cv2.COLOR_GRAY2BGR)

        # Convert header area back to color text on white
        panel_color[:50] = 255
        cv2.putText(panel_color, "EVIDENCE 1: GEOMETRIC FIT (Width Match)",
                    (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        return panel_color

    def create_panel2_contextual_fit(
        self,
        img: np.ndarray,
        gray: np.ndarray,
        redaction: Tuple[int, int, int, int],
        candidate_name: str,
        font_profile: Dict
    ) -> np.ndarray:
        """
        Create Panel 2: Contextual Fit - Shows name in sentence context.

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

        # Draw semi-transparent text
        img_pil = Image.fromarray(overlay)
        draw = ImageDraw.Draw(img_pil, 'RGBA')

        # Create semi-transparent black text
        draw.text((name_x, name_y), candidate_name,
                 font=self.font, fill=(0, 0, 0, 180))

        overlay_with_text = np.array(img_pil)

        # Blend original with overlay (50% opacity)
        blended = cv2.addWeighted(context_crop, 0.5, overlay_with_text, 0.5, 0)

        # Draw red rectangle around the redaction area
        rel_x = x - context_x
        rel_y = y - context_y
        cv2.rectangle(blended, (rel_x, rel_y), (rel_x + w, rel_y + h), (0, 0, 255), 2)

        # Convert to grayscale for header
        blended_gray = cv2.cvtColor(blended, cv2.COLOR_BGR2GRAY)

        # Add header
        panel_with_header = add_safe_header_legacy(
            blended_gray,
            "EVIDENCE 2: CONTEXTUAL FIT (Flows with surrounding text)",
            header_height=50
        )

        # Convert back to color
        panel_color = cv2.cvtColor(panel_with_header, cv2.COLOR_GRAY2BGR)

        # Convert header area to white with black text
        panel_color[:50] = 255
        cv2.putText(panel_color, "EVIDENCE 2: CONTEXTUAL FIT (Flows with surrounding text)",
                    (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        return panel_color

    def create_panel3_artifact_fingerprint(
        self,
        gray: np.ndarray,
        redaction: Tuple[int, int, int, int],
        candidate_name: str,
        highlight_pos: Optional[int] = None
    ) -> np.ndarray:
        """
        Create Panel 3: Artifact Fingerprint - Shows physical remnants.

        Args:
            gray: Grayscale image
            redaction: (x, y, w, h) of redaction box
            candidate_name: Candidate name (for slot mapping)
            highlight_pos: Optional position to highlight (e.g., 6 for 'L')

        Returns:
            Panel image with header and optional annotation
        """
        x, y, w, h = redaction

        # Extract halo data with corner exclusion
        halo_data = self.halo_extractor.extract_halo_with_corner_exclusion(gray, redaction)

        # IMPORTANT: Use ONLY the top wall for ascender detection
        # The top wall is the area directly ABOVE the redaction box
        # This is where ascenders (like 'L', 'h', 'k') would leave artifacts
        # Corners are automatically excluded by the halo_extractor
        top_wall = halo_data['top']

        # Apply forensic enhancement to top wall only (contrast stretching)
        enhanced_top = self.halo_extractor.apply_forensic_enhancement(top_wall)
        contrast_view = enhanced_top['contrast']

        # Create the artifact fingerprint panel
        # Top part: enhanced halo view
        halo_h = 150
        halo_w = 400

        # Resize the halo view for display
        halo_resized = cv2.resize(contrast_view, (halo_w, halo_h))

        # Bottom part: slot map
        # Create a visual representation of character positions
        slot_map_h = 80
        slot_map_w = halo_w

        # Create as COLOR image for artifact highlighting
        slot_map = np.ones((slot_map_h, slot_map_w, 3), dtype=np.uint8) * 255

        # Draw slots for each character position
        num_chars = len(candidate_name)
        slot_width = slot_map_w // (num_chars + 1)

        # Draw slot boundaries
        for i in range(num_chars + 1):
            slot_x = i * slot_width
            cv2.line(slot_map, (slot_x, 0), (slot_x, slot_map_h), (200, 200, 200), 1)

        # Add position labels
        for i in range(num_chars):
            slot_x = i * slot_width + slot_width // 2
            char_label = candidate_name[i] if i < len(candidate_name) else "?"
            cv2.putText(slot_map, f"P{i}:{char_label}", (slot_x - 15, slot_map_h - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 100), 1)

        # AUTOMATIC ARTIFACT DETECTION
        # Analyze the top wall to detect which positions have artifacts
        # Divide top wall into character positions and count dark pixels

        artifact_scores = []
        for i in range(num_chars):
            # Calculate corresponding region in the original top wall
            slot_start_x = int((i * slot_width / slot_map_w) * top_wall.shape[1])
            slot_end_x = int(((i + 1) * slot_width / slot_map_w) * top_wall.shape[1])

            # Extract this slot from the top wall
            slot_region = top_wall[:, slot_start_x:slot_end_x]

            # Count dark pixels (artifacts)
            # Dark pixels = values < 150 (potential anti-aliasing traces)
            dark_pixels = np.sum(slot_region < 150)
            total_pixels = slot_region.size
            artifact_score = (dark_pixels / total_pixels * 100) if total_pixels > 0 else 0

            artifact_scores.append({
                'position': i,
                'char': candidate_name[i] if i < len(candidate_name) else "?",
                'dark_pixels': dark_pixels,
                'artifact_score': artifact_score
            })

        # Color-code the slot map based on detected artifacts
        # Red = high artifact count, Green = low artifact count
        max_score = max([a['artifact_score'] for a in artifact_scores]) if artifact_scores else 1

        for i, score_data in enumerate(artifact_scores):
            slot_x = i * slot_width + 2
            slot_w_actual = slot_width - 4

            # Calculate color intensity based on artifact score
            intensity = int((score_data['artifact_score'] / max_score) * 255) if max_score > 0 else 0

            # Draw colored rectangle behind slot (red = artifacts, green = clean)
            if score_data['artifact_score'] > 2.0:  # Significant artifacts
                color = (0, 0, intensity)  # Red channel
                label = f"{score_data['artifact_score']:.1f}%"
            else:
                color = (0, intensity, 0)  # Green channel (clean)
                label = f"{score_data['artifact_score']:.1f}%"

            # Draw subtle background color
            overlay = slot_map.copy()
            cv2.rectangle(overlay, (slot_x, 0), (slot_x + slot_w_actual, slot_map_h - 20),
                         color, -1)
            cv2.addWeighted(overlay, 0.3, slot_map, 0.7, 0, slot_map)

            # Add score label
            cv2.putText(slot_map, label,
                       (slot_x + 5, 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 0), 1)

        # Print artifact detection results to console
        print(f"\n[*] ARTIFACT DETECTION RESULTS (Top Wall Analysis):")
        print(f"    Position  Character  Dark Pixels  Artifact %")
        print(f"    ---------  ---------  -----------  ----------")
        for score in artifact_scores:
            has_ascender = score['char'] in 'KkLlhHtTbBdDfF'
            indicator = "⚠ ASCENDER" if score['artifact_score'] > 2.0 else "  clean"
            print(f"    {score['position']:2d}        {score['char']:^8s}  {score['dark_pixels']:5d}       "
                  f"{score['artifact_score']:5.1f}%    {indicator}")

        # Combine halo and slot map
        panel_h = halo_h + slot_map_h + 60
        panel_w = halo_w + 40

        # Create panel as COLOR image
        panel = np.ones((panel_h, panel_w, 3), dtype=np.uint8) * 255

        # Add halo view (convert grayscale to color)
        halo_x = (panel_w - halo_w) // 2
        halo_color = cv2.cvtColor(halo_resized, cv2.COLOR_GRAY2BGR)
        panel[20:20+halo_h, halo_x:halo_x+halo_w] = halo_color

        # Add slot map below
        slot_y = 20 + halo_h + 20
        panel[slot_y:slot_y+slot_map_h, halo_x:halo_x+slot_map_w] = slot_map

        # Add annotation if highlight_pos is specified
        if highlight_pos is not None and 0 <= highlight_pos < num_chars:
            # Draw red circle around the position in slot map
            highlight_x = halo_x + highlight_pos * slot_width + slot_width // 2
            highlight_y = slot_y + slot_map_h // 2

            cv2.circle(panel, (highlight_x, highlight_y), 25, (0, 0, 255), 3)

            # Draw arrow pointing to it
            arrow_start = (highlight_x + 40, highlight_y - 30)
            arrow_end = (highlight_x + 10, highlight_y - 10)
            cv2.arrowedLine(panel, arrow_start, arrow_end, (0, 0, 255), 3)

            # Add text annotation
            char = candidate_name[highlight_pos] if highlight_pos < len(candidate_name) else "?"
            annotation_text = f"MATCH: Ascender artifact aligns with letter '{char}'"

            # Split annotation into multiple lines if needed
            y_offset = highlight_y - 50
            cv2.putText(panel, annotation_text[:30], (highlight_x + 50, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            if len(annotation_text) > 30:
                cv2.putText(panel, annotation_text[30:], (highlight_x + 50, y_offset + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # Add header directly for color image
        header_height = 50
        panel_with_header = cv2.copyMakeBorder(
            panel, header_height, 0, 0, 0,
            cv2.BORDER_CONSTANT, value=(255, 255, 255)
        )
        cv2.putText(panel_with_header,
                    "EVIDENCE 3: ARTIFACT FINGERPRINT (Physical remnants match letter structure)",
                    (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

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
        panel3 = self.create_panel3_artifact_fingerprint(gray, redaction, candidate_name, highlight_pos)

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
