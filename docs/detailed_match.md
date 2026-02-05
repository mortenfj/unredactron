# detailed_match.py

## Purpose

**Detailed forensic analysis** of a single high-confidence match. Takes one redaction (e.g. the one that matched "Jeffrey Epstein" at ~81% in pattern matching) and performs deep analysis: extracts the artifact region at 600 DPI, builds an expected template for the candidate name, compares edge patterns by region (top/middle/bottom, left/right), computes overall edge similarity, and produces visual outputs (comparison image and difference map) plus a combined confidence score (width + edge similarity) and a text assessment (STRONG / MODERATE / WEAK MATCH).

## Location

- **Path:** `helpers/detailed_match.py`

## Dependencies

- `cv2`, `numpy`, `pdf2image`, `PIL` (`Image`, `ImageFont`, `ImageDraw`), `os`

## Configuration (Top of File)

| Variable | Meaning | Default |
|----------|---------|---------|
| `FILE_PATH` | Target PDF | `"files/EFTA00037366.pdf"` |
| `FONT_PATH` | Font for template | `"fonts/fonts/times.ttf"` |
| `OUTPUT_DIR` | Directory for comparison images | `"detailed_analysis"` |
| `TARGET_REDACTION` | Redaction box (x, y, w, h) to analyze | `(368, 3531, 713, 107)` |
| `CANDIDATE_NAME` | Candidate text (e.g. from pattern_match) | `"Jeffrey Epstein"` |

Calibration: `SCALE_FACTOR = 10.2346` (from 600 DPI calibration); font size scaled as `12 * 600 / 72`.

## Algorithm

1. **Load document at 600 DPI** — First page to grayscale. Print dimensions.

2. **Extract artifact region** — ROI = redaction box + 30 px padding (clamped). Save region for later steps.

3. **Create template** — Same ROI size; white background. Render `CANDIDATE_NAME` with scaled font, centered vertically; get text bbox. Simulate redaction: black rectangle over text (with small vertical margin). Build halo mask (invert redaction box); extract template halo pixels.

4. **Edge extraction** — Enhance actual artifact (normalize). Canny on actual (50–150 and 20–80). Canny on template halo (50–150 and 20–80). Use strong edges (50–150) for comparison.

5. **Edge analysis** — `analyze_edges(edges, name)`: total edge count; top/middle/bottom third counts; left/right quarter counts. Compare actual vs template for each metric; match % = max(0, 100 - diff/template*100). Print table: Metric, Actual, Template, Match %. Overall similarity = mean of ratios for total, top, bottom (min/max scaled to 100%).

6. **Visual comparison** — Scale 3× for visibility. Actual artifact (with red box), template halo (with red box), actual edges, template edges. Top row: actual | template; bottom row: actual edges | template edges. Save to `OUTPUT_DIR/comparison.png`. Difference map: `absdiff(actual_edges, template_edges)`; save to `OUTPUT_DIR/difference_map.png`.

7. **Forensic assessment** — Width match % = max(0, 100 - |text_w - w|/w*100). Combined score = 0.4×width_match + 0.6×overall_edge_similarity. Assessment: STRONG (>80%), MODERATE (>65%), WEAK (else). Print location, size, candidate, expected vs actual width, width match %, edge similarity %, combined score, assessment, and explanation. Print paths to comparison.png and difference_map.png.

## Output

- Console: step headers, edge analysis table, overall edge similarity %, paths to saved images, forensic assessment (location, size, candidate, widths, scores, assessment, explanation).
- **detailed_analysis/comparison.png** — Side-by-side actual vs expected (artifact and edges).
- **detailed_analysis/difference_map.png** — Pixel-wise edge difference (darker = better match).

## Execution

```bash
python helpers/detailed_match.py
```

Set `TARGET_REDACTION` and `CANDIDATE_NAME` to the redaction and name from a prior run (e.g. helpers/pattern_match.py). Edit `FILE_PATH`, `FONT_PATH`, `OUTPUT_DIR`, and `SCALE_FACTOR` as needed.

## Use Case

- Deep-dive on one redaction after pattern_match (or main) has identified a strong candidate.
- Produce side-by-side and difference images for manual or report use.
- Get a single combined score and STRONG/MODERATE/WEAK assessment.

## See Also

- **pattern_match.md** — Produces high-confidence matches that can be fed into this script.
- **visual_compare.md** — Simpler visual comparison (fixed candidate, outputs to comparisons/).
- **detect_artifacts.md** — Batch artifact detection; this script focuses on one match.
