# find_font_size.py

## Purpose

Finds the **best point size** for a **single** font file. Keeps the control word and font fixed, sweeps font sizes (e.g. 8–18 pt), and ranks by average prediction error against a small set of redaction widths and test names. Prints the best size, scale factor, and a short detailed comparison of predicted vs actual widths.

## Location

- **Path:** `helpers/find_font_size.py`

## Dependencies

- `cv2`, `numpy`, `pytesseract`, `pdf2image`, `PIL.ImageFont`

## Configuration (Top of File)

| Variable | Meaning | Default |
|----------|---------|---------|
| `FILE_PATH` | Target PDF | `"files/EFTA00513855.pdf"` |
| `FONT_PATH` | Single TrueType font file | `"fonts/fonts/times.ttf"` |
| `CONTROL_WORD` | Word used for calibration | `"Contacts"` |
| `TEST_NAMES` | Names used for width prediction vs redaction widths | e.g. JEFFREY EPSTEIN, GHISLAINE MAXWELL, Sarah Kellen, Bill Clinton |

## Algorithm

1. **Load and calibrate**  
   First page to BGR; Tesseract finds first word containing `CONTROL_WORD`, uses its bounding box for `control_width_px` and `control_height_px`.

2. **Redaction detection**  
   Standard pipeline: grayscale, threshold 10 inverted, contours, filter (w>30, h>10, w/h>1.5), sort by y. Script uses a **fixed** list of widths for scoring: `test_redactions = [282, 400, 107]` (three representative widths).

3. **Font size sweep**  
   For each font size from 8 to 18 pt:
   - Load `ImageFont.truetype(FONT_PATH, font_size)`.
   - `control_theoretical = font.getlength(CONTROL_WORD)`, `scale_factor = control_width_px / control_theoretical`.
   - For each redaction width in `test_redactions` and each name in `TEST_NAMES`:
     - `predicted = font.getlength(name) * scale_factor`, accumulate `error = abs(predicted - redaction_width)`.
   - Store `(font_size, avg_error, scale_factor)`.

4. **Ranking**  
   Sort by `avg_error` ascending. Print top 5 sizes with ranking.

5. **Best size summary**  
   Print best size, avg error, scale factor. Then “Detailed analysis” for the best size: for each redaction width in `test_redactions`, a table of each test name with predicted width, error, and “✓ CLOSE” if error < 15.

## Output

- OCR-detected control word and its width×height in pixels.
- “Testing different font sizes…” and separator.
- Table: Font Size, Avg Error (px), Scale Factor, Ranking (top 5).
- “BEST MATCH” block: best pt, avg error, scale factor.
- “Detailed analysis” with best font size: per redaction width, table of name vs predicted vs error and CLOSE marker.

## Execution

```bash
python helpers/find_font_size.py
```

Edit `FILE_PATH`, `FONT_PATH`, `CONTROL_WORD`, `TEST_NAMES`, and optionally `test_redactions` to match your document.

## Use Case

- You already chose a font (e.g. via **find_font.py** or **detect_font.py**) and want to optimize **point size** only.
- Quick sweep over 8–18 pt without changing font file or control word.

## See Also

- **find_font.md** — Picks best **font** at fixed 12 pt.
- **detect_font.md** — Picks best font **and** size using all redactions and multiple sizes.
- **main.md** — Where to set font path and size (e.g. `font_size_pt` in `RedactionCracker`).
