# reconstruct.py

## Purpose

**Forensic text reconstruction** by scoring candidate strings (dictionary words, common names, and brute-force letter patterns) against artifact features. Loads PDF at 600 DPI, finds redactions, calibrates scale (OCR “Subject:” or fallback), then for each redaction in a reasonable size range (100–2000 px width): extracts and enhances the artifact region, analyzes halo edges (total, top, bottom) and sets has_ascenders / has_descenders flags, estimates letter count from width, builds a candidate set (common words, common names, capitalized/uppercase variants, and patterns like “Jeffrey”, “Jennifer”, etc.), scores each candidate with width fit, letter-feature consistency (ascenders/descenders), and edge density, and reports top 5 and any high-confidence (>75%) reconstructions.

## Location

- **Path:** `helpers/reconstruct.py`

## Dependencies

- `cv2`, `numpy`, `pdf2image`, `PIL` (`Image`, `ImageFont`, `ImageDraw`), `os`, `collections.defaultdict`, `pytesseract` (for calibration)

## Configuration (Top of File)

| Variable | Meaning | Default |
|----------|---------|---------|
| `FILE_PATH` | Target PDF | `"files/EFTA00037366.pdf"` |
| `FONT_PATH` | Font for width/theoretical metrics | `"fonts/fonts/times.ttf"` |
| `OUTPUT_DIR` | Directory (created; images not written by default in script) | `"reconstruction"` |

- **LETTER_CATEGORIES** — Ascenders, descenders, serifs, round, vertical letter sets for feature scoring.
- **COMMON_WORDS** — Set of common English/document-style words for candidate generation.
- **COMMON_NAMES** — Set of first names (Sarah, Ghislaine, Jeffrey, etc.) for candidate generation.

## Algorithm

1. **Load at 600 DPI** — First page to grayscale. Print size.

2. **Find redactions** — Threshold 15 inverted, contours; filter w>30, h>10, w/h>1.5.

3. **Calibration** — Tesseract on grayscale; find word containing “Subject:”, use its width; compute SCALE_FACTOR (e.g. 2.8998 * 600/170) or use fallback 10.23. Load font at 12 pt and scaled size (12*600/72) for rendering.

4. **ArtifactAnalyzer** — Class holding gray image, scale, font. Methods:
   - **extract_artifacts(x,y,w,h,padding=10):** ROI with padding, normalize, Canny(30,100); return roi, enhanced, edges.
   - **analyze_features(edges, box_x, box_y, box_w, box_h):** Halo mask (invert box), halo_edges; count total, top_region (10 px above), bottom_region (10 px below); return total_edges, top_edges, bottom_edges, has_ascenders (top>50), has_descenders (bottom>50).
   - **score_candidate(candidate_text, actual_width, features):** Expected width = font.getlength(candidate)*scale; width_score from difference; feature_score from ascender/descender consistency with candidate; edge_score from ratio of expected vs total_edges; combined = 0.5*width + 0.3*feature + 0.2*edge. Return dict of scores and expected_width.

5. **Per redaction (100 < w < 2000)** — Extract artifacts, get features. Estimate letter_count from w / (50*SCALE_FACTOR/10), clamp 2–15. Build candidates: COMMON_WORDS with length near letter_count; COMMON_NAMES with length near letter_count (note: code uses `word` in one place where it may intend `name`); capitalized/upper variants; patterns like “Jeffrey”, “Jennifer”, “Bill”, “David” with common first letters. Score all candidates; sort by combined. Print top 5 with status STRONG/MODERATE/WEAK; append to results if combined > 75.

6. **Summary** — Sort results by score; print high-confidence reconstructions (redaction position, width, reconstructed text, confidence). If none, print possible reasons.

## Output

- Console: step headers, redaction count; per redaction: position/size, features (edge count, ascenders/descenders), estimated letter count, “Testing N candidates”, top 5 candidates with scores and status; final “RECONSTRUCTION SUMMARY” with high-confidence reconstructions or “No high-confidence reconstructions” and caveats.

## Execution

```bash
python helpers/reconstruct.py
```

Edit `FILE_PATH`, `FONT_PATH`, calibration control word, COMMON_WORDS, COMMON_NAMES, and letter patterns as needed.

## Use Case

- Suggest possible redacted words/names from artifact shape and width without assuming a fixed suspect list.
- Combine geometric (width), typographic (ascenders/descenders), and edge-density cues.

## See Also

- **letter_reconstruction.md** — Letter-by-letter slot analysis from edge signatures.
- **pattern_match.md** — Full-name template matching.
- **main.md** — Width-only matching against a fixed SUSPECT_LIST.
