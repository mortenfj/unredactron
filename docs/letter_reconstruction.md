# letter_reconstruction.py

## Purpose

**Letter-by-letter reconstruction** from artifact patterns. Loads the PDF at 600 DPI, finds name-sized redactions (150 < width < 800), builds a per-letter “signature” database (edge counts in top/bottom/left/right regions, ascender/descender flags) from the calibrated font, then for each redaction (first 5) extracts the halo, divides the width into letter “slots,” scores each slot’s top/bottom edge counts against every letter signature, and attempts a best-letter-per-slot reconstruction. Saves a visualization per redaction to `letter_analysis/`.

## Location

- **Path:** `helpers/letter_reconstruction.py`

## Dependencies

- `cv2`, `numpy`, `pdf2image`, `PIL` (`Image`, `ImageFont`, `ImageDraw`), `os`

## Configuration (Top of File)

| Variable | Meaning | Default |
|----------|---------|---------|
| `FILE_PATH` | Target PDF | `"files/EFTA00037366.pdf"` |
| `FONT_PATH` | Font for letter templates | `"fonts/fonts/times.ttf"` |
| `OUTPUT_DIR` | Directory for analysis images | `"letter_analysis"` |

Calibration: `SCALE_FACTOR = 10.2346`; font size at 600 DPI = `12 * 600 / 72`.

## Algorithm

1. **Load at 600 DPI** — First page to grayscale.

2. **Find redactions** — Threshold 15 inverted, contours; keep boxes with 150 < w < 800 and h > 10 (name-sized). Sort not specified; uses first 5 for analysis.

3. **Letter signature database** — For each character in `"A..Z a..z"`: render on 200×200 template, Canny(50,150). For each letter compute: top_half / bottom_half / left_quarter / right_quarter edge counts, total edges; ascender = top_edges > bottom_edges*1.5, descender = bottom_edges > top_edges*1.5. Store width (font.getlength(letter)*SCALE_FACTOR) and all counts/flags in `letter_signatures`.

4. **Per redaction (first 5)** — Extract ROI with 20 px padding. Enhance (normalize), Canny(20,80). Redaction box position within ROI: box_x, box_y. Top strip: 8 px above box; bottom strip: 8 px below box (for ascender/descender traces).

5. **Letter slots** — Estimate letter count: `num_letters = round(w / 55)` clamped to 3–15. Slot width = w / num_letters. For each slot: extract slot from top_strip and bottom_strip; count edge pixels in slot (top_edges_count, bottom_edges_count). For each letter, compare to signature (top_diff, bottom_diff); similarity = 100*(1 - (top_diff + bottom_diff)/(2*max_edges)). Sort by similarity; keep top 3 per slot; print position, edge counts, and top 3 letters with score and ascender/descender if relevant.

6. **Reconstruction** — Best letter per slot = highest-scoring letter with score > 60; else `?`. Print “Best reconstruction: …”. Save visualization (enhanced ROI with redaction box in red) to `OUTPUT_DIR/redaction_{i+1}_analysis.png`.

## Output

- Console: step headers, number of target redactions, letter DB size; for each of first 5 redactions: position/size, estimated letter count, per-slot analysis (edges, top 3 letters), best reconstruction string.
- **letter_analysis/redaction_1_analysis.png** … **redaction_5_analysis.png** — Enhanced artifact with redaction outline.

## Execution

```bash
python helpers/letter_reconstruction.py
```

Edit `FILE_PATH`, `FONT_PATH`, `OUTPUT_DIR`, and `SCALE_FACTOR` as needed. Redaction filter (150 < w < 800) and “first 5” limit are hardcoded.

## Use Case

- Attempt to infer individual letters from artifact edges (ascenders/descenders, horizontal position).
- Research/experimentation; reconstructions are heuristic and may be noisy.

## See Also

- **reconstruct.md** — Candidate-based scoring with dictionary/name lists and ascender/descender features.
- **pattern_match.md** — Full-name template vs artifact edges.
- **detect_artifacts.md** — Batch artifact extraction.
