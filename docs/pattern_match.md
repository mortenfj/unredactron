# pattern_match.py

## Purpose

**Advanced pattern matching** between rendered suspect names and artifact regions: load PDF at **600 DPI**, find redactions, render each suspect name at the correct scale for 600 DPI, extract edges from the template and from the “halo” (region around each redaction), and score matches by edge ratio and width fit. Reports best match per name and a confidence level (HIGH/MEDIUM/LOW).

## Location

- **Path:** `helpers/pattern_match.py`

## Dependencies

- `cv2`, `numpy`, `pdf2image`, `PIL` (`Image`, `ImageFont`, `ImageDraw`), `os`

## Configuration (Top of File)

| Variable | Meaning | Default |
|----------|---------|---------|
| `FILE_PATH` | Target PDF | `"files/EFTA00037366.pdf"` |
| `FONT_PATH` | Font for rendering names | `"fonts/fonts/times.ttf"` |
| `DPI_RATIO` | 600/170 (scale from default PDF render to 600 DPI) | ~3.53 |
| `SCALE_FACTOR` | Document scale factor adjusted for 600 DPI (e.g. 2.8998 × DPI_RATIO) | Precomputed |
| `FONT_SIZE` | Point size for theoretical width | 12 |
| `SUSPECT_NAMES` | List of names to match | e.g. Bill Clinton, Jeffrey Epstein, … |

## Algorithm

1. **Load at 600 DPI**  
   `convert_from_path(FILE_PATH, dpi=600)`, first page to grayscale. Print dimensions.

2. **Find redactions**  
   Threshold 15 inverted, contours, filter (w>30, h>10, w/h>1.5). Same logic as **detect_artifacts.py** at 600 DPI.

3. **For each suspect name**  
   - **Expected width at 600 DPI:** `text_width_theoretical = font.getlength(name)`, `expected_width = text_width_theoretical * SCALE_FACTOR`.
   - **Matching redactions:** Redactions where `abs(w - expected_width) < expected_width * 0.1` (within 10%).
   - **Template:** Create grayscale image; font size scaled for 600 DPI: `scaled_font_size = FONT_SIZE * 600 / 72`, draw name, extract edges with Canny(50, 150). Count template edge pixels.
   - **For each matching redaction:** Extract artifact ROI (redaction + padding 10). Build halo mask (region outside redaction inside ROI). Canny on enhanced ROI; count edge pixels in halo. Compute:
     - `edge_ratio = min(template_edges, artifact_edges) / max(...)`.
     - `width_quality = max(0, 1 - width_diff/expected_width)`.
     - `combined_score = 0.5*edge_ratio + 0.5*width_quality`.
   - Keep best match (highest score) for this name. Append to results.

4. **Summary**  
   Sort results by score descending. For each: name, location, size, match score, confidence (HIGH >0.7, MEDIUM >0.5, else LOW). If score > 0.7, print “STRONG MATCH”. Else print short explanation (clean redactions, wrong names, or font mismatch).

## Output

- “PATTERN MATCHING” header.
- STEP 1: Image size at 600 DPI.
- STEP 2: Number of redaction boxes.
- STEP 3: Per name, “Analyzing: ‘Name’”, expected width, number of matching redactions, template size and edge count; best match position, width vs expected, template/artifact edge counts, match score.
- “PATTERN MATCHING RESULTS”: for each result, name, location, size, score, confidence; optional “STRONG MATCH” or caveats.

## Execution

```bash
python helpers/pattern_match.py
```

Ensure `SCALE_FACTOR` is correct for your document at 600 DPI (e.g. from a previous calibration scaled by DPI_RATIO). Edit `FILE_PATH`, `FONT_PATH`, `SUSPECT_NAMES`, and calibration constants as needed.

## Use Case

- After geometric width matching, add a **second signal** from edge patterns in the halo.
- Use when you have high-DPI rendering and want to see if artifact edges align with a rendered name (anti-aliasing traces).

## See Also

- **detect_artifacts.md** — Generates artifact images and simpler template matching.
- **analyze_artifacts.md** — Analyzes saved artifact images (brightness, distribution).
- **main.md** — Geometric width-only matching; no edge pattern scoring.
