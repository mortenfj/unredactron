# detect_artifacts.py

## Purpose

Detects potential **text traces (artifacts)** around redaction boxes by rendering the PDF at **600 DPI**, finding redaction boxes, and analyzing the “halo” region (a few pixels around each box) for non-black pixels, edges, and protrusions. Can save enhanced images of halo regions and run a simple template-based comparison of suspect names to artifact edges.

## Location

- **Path:** `helpers/detect_artifacts.py`

## Dependencies

- `cv2`, `numpy`, `pdf2image`, `PIL` (`Image`, `ImageFont`, `ImageDraw`), `os`

## Configuration (Top of File)

| Variable | Meaning | Default |
|----------|---------|---------|
| `FILE_PATH` | Target PDF | `"files/EFTA00037366.pdf"` |
| `FONT_PATH` | Font for rendering name templates | `"fonts/fonts/times.ttf"` |
| `OUTPUT_DIR` | Directory for saved artifact images | `"artifacts"` |

## Algorithm

### STEP 1: High-DPI conversion

- `convert_from_path(FILE_PATH, dpi=600)` for first page.
- Convert to grayscale. Print image dimensions.

### STEP 2: Redaction detection

- Threshold 15 (inverted) on grayscale to get black mask.
- Contours, filter: `w > 30`, `h > 10`, `w/h > 1.5`, sort by y.
- Same logic as main engine but at 600 DPI (larger pixel counts).

### STEP 3: Halo analysis per redaction

For each redaction `(x, y, w, h)`:

- **ROI:** Box extended by `padding = 8` pixels on all sides (clamped to image).
- **Box mask:** Rectangle covering the redaction inside the ROI.
- **Halo mask:** Invert box mask so halo = region outside the redaction but inside ROI.
- **Halo pixels:** Pixel values in the halo region.

**Metrics computed:**

1. **Brightness:** mean, min, max, std of halo pixels.
2. **Suspicious pixels:** Count of pixels with value in (20, 235). Ratio = suspicious / total halo pixels × 100.
3. **Edges:** Canny(30, 100) on halo; count of edge pixels.
4. **Protrusions:** Strips 2 px above and below the box; count of dark pixels (< 50) in those strips.

**Flag:** `has_artifacts = True` if any of: `suspicious_ratio > 1.0`, `edge_count > 50`, `top_protrusions > 5`, `bottom_protrusions > 5`.

If `has_artifacts`, save an enhanced (normalized) halo image with the redaction box drawn in red to `OUTPUT_DIR/artifact_NNN_xX_yY.png`.

### STEP 4: Template matching (suspect names)

- **SUSPECT_NAMES:** Fixed list (e.g. Sarah Kellen, Ghislaine Maxwell, …).
- Font loaded at 12 pt. For each name:
  - Render name on a white template image, get text bbox.
  - Find redactions whose width is within 15 px of the rendered text width.
  - For each such redaction: extract artifact ROI, Canny on ROI and on template, count edge pixels. Compute edge similarity and width quality; combined score = 0.3×edge_similarity + 0.7×width_quality.
  - If combined score > 80%, print match with width and scores.

## Output

- Step-by-step headers (STEP 1–4).
- Image size at 600 DPI, number of redaction boxes.
- “ARTIFACT ANALYSIS SUMMARY”: count of boxes with potential artifacts; for each such box, index, position, size, and which signals fired; paths to saved images.
- “STEP 4: Template Matching”: for each suspect name, matching redactions and scores.
- “ANALYSIS COMPLETE” and path to `OUTPUT_DIR/`.

## Execution

```bash
python helpers/detect_artifacts.py
```

Creates `OUTPUT_DIR` if missing. Edit `FILE_PATH`, `FONT_PATH`, `OUTPUT_DIR`, and `SUSPECT_NAMES` as needed.

## Use Case

- Look for anti-aliasing or residual text at redaction edges (halo).
- Generate artifact images for manual inspection or for **analyze_artifacts.py**.
- Rough template-based check of whether a name’s width and edge pattern align with a redaction.

## See Also

- **analyze_artifacts.md** — Reads saved artifact images and reports halo stats.
- **pattern_match.md** — More advanced pattern matching at 600 DPI with scaled font and halo edges.
- **unredactron.md** — `artifact_check` placeholder in the main engine.
