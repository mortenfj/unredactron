# find_font.py

## Purpose

Tests **all** fonts in a directory against a **fixed** control word and a small set of **sample redaction widths**. Ranks fonts by average prediction error (lower is better) and prints a recommended font. Useful when you already know a good control word and a few representative redaction widths.

## Location

- **Path:** `helpers/find_font.py`

## Dependencies

- `cv2`, `numpy`, `pytesseract`, `pdf2image`, `PIL.ImageFont`, `os`

## Configuration (Top of File)

| Variable | Meaning | Default |
|----------|---------|---------|
| `FILE_PATH` | Target PDF | `"files/EFTA00513855.pdf"` |
| `CONTROL_WORD` | Word used for calibration (must appear on page) | `"Contacts"` |
| `FONTS_DIR` | Directory with `.ttf` / `.TTF` files | `"fonts/fonts/"` |
| `TEST_NAMES` | Names used to compute predicted width vs sample redaction widths | e.g. JEFFREY EPSTEIN, GHISLAINE MAXWELL, Sarah Kellen, Bill Clinton |

## Algorithm

1. **Load and calibrate**  
   - Converts first page to BGR.  
   - Runs Tesseract; finds first word containing `CONTROL_WORD` (case-insensitive) and uses its bounding box.  
   - `control_width_px` = width from OCR.

2. **Redaction blocks**  
   Same pipeline as main engine: grayscale, threshold 10 inverted, contours, filter (w>30, h>10, w/h>1.5), sort by y. The script does **not** use all redactions for scoring; it uses a fixed list of widths (see below).

3. **Sample redaction widths**  
   Hardcoded list of widths and labels used for testing, e.g.:
   - 282 px (“Block #5” — close to “JEFFREY EPSTEIN” with Times)
   - 400 px (“Block #2” — large)
   - 107 px (“Block #1” — small)

4. **Font test**  
   For each font file (sorted), at **12 pt** only:
   - Load font, compute `scale_factor = control_width_px / font.getlength(CONTROL_WORD)`.
   - For each `(redaction_width, redaction_name)` in the sample list and each name in `TEST_NAMES`:
     - `predicted = font.getlength(name) * scale_factor`, `error = abs(predicted - redaction_width)`.
   - Average error over all (redaction_width, name) pairs. Store `(font_file, avg_error)`.

5. **Ranking**  
   Sort by `avg_error` ascending. Print top 10 with ranking (medals for top 3). Print “RECOMMENDED FONT” and average error for the best.

## Output

- Calibration line: control word and its pixel width in the document.
- “Testing N fonts…” and a separator.
- Table: Font File, Average Error (px), Ranking (top 10).
- “RECOMMENDED FONT” block with best font and average error.

## Execution

```bash
python helpers/find_font.py
```

Edit `FILE_PATH`, `CONTROL_WORD`, `FONTS_DIR`, and optionally the hardcoded `test_redactions` list and `TEST_NAMES` to match your document.

## Use Case

- You have a known control word (e.g. “Contacts”) and a few redaction widths you care about.
- You want a quick “which font fits best?” answer without scanning all redactions or multiple font sizes (unlike **detect_font.py**).
- Single font size (12 pt) keeps the script simple; use **find_font_size.py** to refine size for one font.

## See Also

- **detect_font.md** — Uses OCR-selected control word and **all** redactions, multiple font sizes.
- **find_font_size.md** — Fixes one font and sweeps point size.
- **main.md** — Where to set the chosen font path.
