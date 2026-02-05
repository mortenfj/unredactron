# detect_font.py

## Purpose

Automatically finds the best-matching font and point size for a document by testing **all** fonts in a directory at multiple sizes, calibrating each with a control word from OCR, and ranking by **average error** when predicting redaction block widths using a fixed set of test names.

## Location

- **Path:** `helpers/detect_font.py`

## Dependencies

- `cv2`, `numpy`, `pytesseract`, `pdf2image`, `PIL.ImageFont`, `os`

## Configuration (Top of File)

| Variable | Meaning | Default |
|----------|---------|---------|
| `FILE_PATH` | Target PDF | `"files/EFTA00037366.pdf"` |
| `FONTS_DIR` | Directory containing `.ttf` / `.TTF` files | `"fonts/fonts/"` |
| `TEST_NAMES` | Names used to compute prediction error vs redaction widths | e.g. Bill Clinton, JEFFREY EPSTEIN, GHISLAINE MAXWELL, Sarah Kellen |

## Algorithm

1. **Load document**  
   Converts first page to BGR with `convert_from_path` and `cv2.cvtColor`.

2. **Control word selection**  
   - Runs Tesseract `image_to_data`.  
   - Keeps words with confidence > 80, length 5–15, and first character uppercase.  
   - Uses the **first** such word as `CONTROL_WORD` and its OCR width as `CONTROL_WIDTH` / `CONTROL_HEIGHT`.

3. **Redaction detection**  
   Same logic as the main engine: grayscale → threshold 10 (inverted) → contours → filter `w > 30`, `h > 10`, `w/h > 1.5`, sort by y.

4. **Font sweep**  
   For each font file in `FONTS_DIR` and each font size in `[10, 11, 12, 13, 14]`:
   - Load font with `ImageFont.truetype(font_path, font_size)`.
   - Compute `scale_factor = CONTROL_WIDTH / font.getlength(CONTROL_WORD)`.
   - For every redaction `(x, y, w, h)` and every `name` in `TEST_NAMES`:
     - `predicted = font.getlength(name) * scale_factor`.
     - Accumulate `error = abs(predicted - w)` and count “close” matches (error ≤ 15).
   - Store: font file, size, scale_factor, avg_error, match_rate (%), close_matches, tests.

5. **Ranking**  
   Results sorted by **avg_error** (ascending). Top 15 printed with a short ranking (medals for top 3).

6. **Recommendation**  
   Prints the best font/size, scale factor, average error, and match rate. Then prints a short “spacing analysis”: character widths (sample letters A–J) and sample name width predictions for the best font.

## Output

- Header and document info (path, pages, image size).
- List of potential control words (first 10) and the selected one with its pixel width.
- Number of redaction blocks found.
- Table: Font, Size, Scale, Avg Error, Match Rate, Ranking (top 15).
- “RECOMMENDED FONT” block with best font, size, scale factor, avg error, match rate.
- “SPACING ANALYSIS”: character widths (A–J) and sample name predictions for the best font.

## Execution

```bash
python helpers/detect_font.py
```

Adjust `FILE_PATH` and `FONTS_DIR` if needed. No command-line arguments.

## Use Case

Use when you do **not** know the document font. The script picks a control word from OCR, finds redactions, and reports which font and size minimize prediction error across all redactions and test names. You can then set `FONT_PATH` and font size in `main.py` or `unredactron.py` accordingly.

## See Also

- **detect_font_v2.md** — Font detection using **visible text** consistency (multiple OCR words) instead of redaction widths.
- **find_font.md** — Simpler font test against a fixed control word and a few redaction widths.
- **find_font_size.md** — Best point size for a **single** font file.
- **main.md** — Where to set the chosen font path and size.
