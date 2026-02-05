# visual_compare.py

## Purpose

**Visual comparison** of the actual artifact region vs the expected pattern for a single candidate name. Loads the PDF at 600 DPI, extracts the artifact ROI around a fixed redaction (e.g. the “Jeffrey Epstein” match), creates a template of that name with a simulated redaction and halo, runs Canny on both actual and expected halo, and saves numbered images to `comparisons/`: actual artifact, actual edges, expected template, template with redaction, expected edges, side-by-side comparison (artifact + edges), and edge-only comparison. No scoring; output is for manual inspection.

## Location

- **Path:** `helpers/visual_compare.py`

## Dependencies

- `cv2`, `numpy`, `pdf2image`, `PIL` (`Image`, `ImageFont`, `ImageDraw`), `os`

## Configuration (Top of File)

| Variable | Meaning | Default |
|----------|---------|---------|
| `FILE_PATH` | Target PDF | `"files/EFTA00037366.pdf"` |
| `FONT_PATH` | Font for expected text | `"fonts/fonts/times.ttf"` |
| `OUTPUT_DIR` | Directory for comparison images | `"comparisons"` |
| `MATCH_NAME` | Candidate name to compare | `"Jeffrey Epstein"` |
| `MATCH_X`, `MATCH_Y` | Redaction top-left | `368`, `3531` |
| `MATCH_W`, `MATCH_H` | Redaction size | `713`, `107` |

Calibration: `DPI_RATIO = 600/170`, `SCALE_FACTOR = 2.8998 * DPI_RATIO`, `FONT_SIZE = 12`.

## Algorithm

1. **Load at 600 DPI** — First page to grayscale.

2. **Extract actual artifact** — ROI = redaction box + 15 px padding. Normalize; save as `01_actual_artifact.png`. Canny(30,100) on enhanced ROI; save as `02_actual_edges.png`.

3. **Create expected template** — Same ROI dimensions; white background. Scaled font size = 12*600/72. Draw MATCH_NAME centered vertically at (padding, …). Convert to numpy. Simulate redaction: black rectangle over text (with 5 px vertical margin). Build halo mask (invert redaction); bitwise_and to get template halo. Save full template as `03_expected_template.png`, template with redaction as `04_template_with_redaction.png`. Canny(50,150) on template halo; save as `05_expected_edges.png`.

4. **Comparison images** — Scale 2×. Actual enhanced and template halo to BGR; add labels “ACTUAL ARTIFACT” and “EXPECTED PATTERN”; hstack; save `06_comparison.png`. Actual edges and template edges to BGR; labels “ACTUAL EDGES” and “EXPECTED EDGES”; hstack; save `07_edge_comparison.png`.

5. **Summary** — Print paths and short description of key files (01, 02, 05, 07) and that close edge match suggests the candidate is the redacted text.

## Output

- **comparisons/01_actual_artifact.png** — Enhanced actual ROI.
- **comparisons/02_actual_edges.png** — Canny edges of actual ROI.
- **comparisons/03_expected_template.png** — Rendered name (no redaction).
- **comparisons/04_template_with_redaction.png** — Template with black redaction box.
- **comparisons/05_expected_edges.png** — Canny edges of expected halo.
- **comparisons/06_comparison.png** — Side-by-side actual vs expected (grayscale regions).
- **comparisons/07_edge_comparison.png** — Side-by-side actual edges vs expected edges.

Console: step messages and “Key files to examine” with interpretation hint.

## Execution

```bash
python helpers/visual_compare.py
```

Set `MATCH_NAME`, `MATCH_X`, `MATCH_Y`, `MATCH_W`, `MATCH_H` from a prior run (e.g. pattern_match or main). Edit `FILE_PATH`, `FONT_PATH`, `OUTPUT_DIR`, and calibration if needed.

## Use Case

- Produce a fixed set of comparison images for one redaction and one candidate for reports or manual review.
- Lighter weight than detailed_match.py (no scoring or difference map).

## See Also

- **detailed_match.md** — Single-match deep analysis with scoring and difference map.
- **pattern_match.md** — Finds matches that can be passed to this script (name + position/size).
- **detect_artifacts.md** — Batch artifact extraction and template matching.
