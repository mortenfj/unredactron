#!/usr/bin/env python3
"""
Margin-Safe Labeling Utilities for Forensic Image Generation

This module provides functions to add text labels to forensic images WITHOUT
drawing over the actual forensic content. All text is placed in dedicated
headers, footers, or gutters to preserve pixel-perfect artifact integrity.

Critical for digital forensics: No text should ever obscure anti-aliasing
artifacts or other subtle pixel patterns that may be evidentiary.
"""

import cv2
import numpy as np
from typing import Tuple, Optional, List


def add_safe_header(
    base_img: np.ndarray,
    label_text: str,
    header_height: int = 40,
    font_scale: float = 0.6,
    text_color: Tuple[int, int, int] = (0, 0, 0),
    bg_color: int = 255
) -> np.ndarray:
    """
    Adds a white header to an image so text never touches the actual forensic content.

    Args:
        base_img: Input grayscale (H, W) or BGR (H, W, 3) image
        label_text: Text to display in the header
        header_height: Height of the header in pixels
        font_scale: Scale factor for the font
        text_color: Text color (B, G, R) for color or grayscale value for grayscale
        bg_color: Background color (0-255)

    Returns:
        New image with header stacked on top (header_height + H, W)
    """
    is_color = len(base_img.shape) == 3
    h, w = base_img.shape[:2]

    # Add header using copyMakeBorder
    if is_color:
        result = cv2.copyMakeBorder(base_img, header_height, 0, 0, 0,
                                    cv2.BORDER_CONSTANT, value=(bg_color, bg_color, bg_color))
    else:
        result = cv2.copyMakeBorder(base_img, header_height, 0, 0, 0,
                                    cv2.BORDER_CONSTANT, value=bg_color)

    # Draw text in the header area
    text_y = int(header_height * 0.65)
    cv2.putText(result, label_text, (10, text_y),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, 1)

    return result


def add_safe_footer(
    base_img: np.ndarray,
    label_text: str,
    footer_height: int = 40,
    font_scale: float = 0.6,
    text_color: Tuple[int, int, int] = (0, 0, 0),
    bg_color: int = 255
) -> np.ndarray:
    """
    Adds a white footer below an image for diagnostic information.

    Args:
        base_img: Input grayscale (H, W) or BGR (H, W, 3) image
        label_text: Text to display in the footer
        footer_height: Height of the footer in pixels
        font_scale: Scale factor for the font
        text_color: Text color (B, G, R) for color or grayscale value for grayscale
        bg_color: Background color (0-255)

    Returns:
        New image with footer stacked below (H + footer_height, W)
    """
    is_color = len(base_img.shape) == 3
    h, w = base_img.shape[:2]

    # Add footer using copyMakeBorder
    if is_color:
        result = cv2.copyMakeBorder(base_img, 0, footer_height, 0, 0,
                                    cv2.BORDER_CONSTANT, value=(bg_color, bg_color, bg_color))
    else:
        result = cv2.copyMakeBorder(base_img, 0, footer_height, 0, 0,
                                    cv2.BORDER_CONSTANT, value=bg_color)

    # Draw text in the footer area
    text_y = h + int(footer_height * 0.65)
    cv2.putText(result, label_text, (10, text_y),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, 1)

    return result


def add_multi_line_footer(
    base_img: np.ndarray,
    lines: List[str],
    footer_height: int = None,
    font_scale: float = 0.5,
    text_color: Tuple[int, int, int] = (0, 0, 0),
    bg_color: int = 255
) -> np.ndarray:
    """
    Adds a multi-line footer for detailed diagnostic information.

    Args:
        base_img: Input grayscale (H, W) or BGR (H, W, 3) image
        lines: List of text lines to display
        footer_height: Height of the footer (auto-calculated if None)
        font_scale: Scale factor for the font
        text_color: Text color (B, G, R) for color or grayscale value for grayscale
        bg_color: Background color (0-255)

    Returns:
        New image with footer stacked below
    """
    if footer_height is None:
        # Auto-calculate: ~20px per line + padding
        footer_height = len(lines) * 20 + 10

    is_color = len(base_img.shape) == 3
    h, w = base_img.shape[:2]

    # Add footer using copyMakeBorder
    if is_color:
        result = cv2.copyMakeBorder(base_img, 0, footer_height, 0, 0,
                                    cv2.BORDER_CONSTANT, value=(bg_color, bg_color, bg_color))
    else:
        result = cv2.copyMakeBorder(base_img, 0, footer_height, 0, 0,
                                    cv2.BORDER_CONSTANT, value=bg_color)

    # Draw each line in the footer area
    line_height = 20
    for i, line in enumerate(lines):
        text_y = h + 15 + (i * line_height)
        if text_y < h + footer_height:
            cv2.putText(result, line, (10, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, 1)

    return result


def create_labeled_grid(
    images: List[np.ndarray],
    labels: List[str],
    cols: int = 2,
    gutter_size: int = 30,
    header_height: int = 40,
    text_color: Tuple[int, int, int] = (0, 0, 0),
    bg_color: int = 255
) -> np.ndarray:
    """
    Creates a grid of images with headers, ensuring text never overlays content.

    Args:
        images: List of images to arrange in a grid
        labels: List of labels (one per image)
        cols: Number of columns in the grid
        gutter_size: White space between images
        header_height: Height of each image's header
        text_color: Text color
        bg_color: Background color

    Returns:
        Composite image with proper gutters and headers
    """
    if len(images) != len(labels):
        raise ValueError("Number of images must match number of labels")

    # Add headers to all images
    labeled_images = []
    for img, label in zip(images, labels):
        labeled = add_safe_header(
            img, label, header_height, 0.6, text_color, bg_color
        )
        labeled_images.append(labeled)

    # Calculate grid dimensions
    rows = (len(labeled_images) + cols - 1) // cols

    # Get max dimensions for each cell
    max_height = max(img.shape[0] for img in labeled_images)
    max_width = max(img.shape[1] for img in labeled_images)

    # Pad all images to same size
    padded_images = []
    for img in labeled_images:
        is_color = len(img.shape) == 3
        h, w = img.shape[:2]

        # Add white padding to match max dimensions
        top_pad = 0
        bottom_pad = max_height - h
        left_pad = 0
        right_pad = max_width - w

        if is_color:
            padded = cv2.copyMakeBorder(
                img, top_pad, bottom_pad, left_pad, right_pad,
                cv2.BORDER_CONSTANT, value=(bg_color, bg_color, bg_color)
            )
        else:
            padded = cv2.copyMakeBorder(
                img, top_pad, bottom_pad, left_pad, right_pad,
                cv2.BORDER_CONSTANT, value=bg_color
            )
        padded_images.append(padded)

    # Build grid rows
    row_images = []
    for r in range(rows):
        row_images_list = []
        for c in range(cols):
            idx = r * cols + c
            if idx < len(padded_images):
                row_images_list.append(padded_images[idx])

        # Add horizontal gutters between images in row
        if row_images_list:
            row_with_gutters = []
            for i, img in enumerate(row_images_list):
                row_with_gutters.append(img)
                if i < len(row_images_list) - 1:
                    # Create gutter
                    next_img = row_images_list[i + 1]
                    gutter_h = next_img.shape[0]
                    gutter_is_color = len(next_img.shape) == 3
                    if gutter_is_color:
                        gutter = np.empty((gutter_h, gutter_size, 3), dtype=np.uint8)
                        gutter.fill(bg_color)
                    else:
                        gutter = np.empty((gutter_h, gutter_size), dtype=np.uint8)
                        gutter.fill(bg_color)
                    row_with_gutters.append(gutter)

            row = np.hstack(row_with_gutters)
            row_images.append(row)

    # Add vertical gutters between rows
    if row_images:
        final_rows = []
        for i, row in enumerate(row_images):
            final_rows.append(row)
            if i < len(row_images) - 1:
                # Create gutter
                gutter_w = row.shape[1]
                row_is_color = len(row.shape) == 3
                if row_is_color:
                    gutter = np.empty((gutter_size, gutter_w, 3), dtype=np.uint8)
                    gutter.fill(bg_color)
                else:
                    gutter = np.empty((gutter_size, gutter_w), dtype=np.uint8)
                    gutter.fill(bg_color)
                final_rows.append(gutter)

        return np.vstack(final_rows)

    # Fallback for empty grid
    return labeled_images[0] if labeled_images else np.array([])


def add_side_annotation(
    base_img: np.ndarray,
    annotation_text: str,
    side: str = 'left',
    sidebar_width: int = 150,
    font_scale: float = 0.5,
    text_color: Tuple[int, int, int] = (0, 0, 0),
    bg_color: int = 255
) -> np.ndarray:
    """
    Adds a sidebar annotation to the left or right of an image.

    Useful for adding arrows or pointers that reference image content
    without drawing over it.

    Args:
        base_img: Input grayscale (H, W) or BGR (H, W, 3) image
        annotation_text: Text to display in sidebar
        side: 'left' or 'right'
        sidebar_width: Width of the sidebar in pixels
        font_scale: Scale factor for the font
        text_color: Text color
        bg_color: Background color

    Returns:
        New image with sidebar added
    """
    is_color = len(base_img.shape) == 3
    h, w = base_img.shape[:2]

    # Create sidebar
    if is_color:
        sidebar = np.ones((h, sidebar_width, 3), dtype=np.uint8) * bg_color
    else:
        sidebar = np.ones((h, sidebar_width), dtype=np.uint8) * bg_color

    # Draw text (wrapped to fit sidebar width)
    # Simple word wrap
    words = annotation_text.split()
    lines = []
    current_line = ""
    max_chars_per_line = int(sidebar_width / 8)  # Approximate

    for word in words:
        test_line = current_line + " " + word if current_line else word
        if len(test_line) <= max_chars_per_line:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    # Draw lines
    line_height = 20
    start_y = 30
    for i, line in enumerate(lines):
        text_y = start_y + (i * line_height)
        if text_y < h:
            cv2.putText(sidebar, line, (10, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, 1)

    # Stack sidebar and image
    if side == 'left':
        return np.hstack([sidebar, base_img])
    else:
        return np.hstack([base_img, sidebar])
