# detect_font_v2.py

## Purpose

Finds the best-matching font and point size by comparing **OCR measurements of visible text** to each font’s theoretical text width. The best match is the font/size for which the implied scale factor is most **consistent** across many visible words (lowest coefficient of variation), rather than by fitting redaction widths.

## Location

- **Path:** `helpers/detect_font_v2.py`

## Dependencies

- `cv2`, `numpy`, `pytesseract`, `pdf2image`, `PIL.ImageFont`, `os`

## Configuration (Top of File)

| Variable | Meaning | Default |
|----------|---------|---------|
| `FILE_PATH` | Target PDF | `"files/EFTA00037366.pdf"` |
| `FONTS_DIR` | Directory with `.ttf` / `.TTF` files | `"fonts/fonts/"` |

## Algorithm

1. **Load document**  
   First page converted to BGR.

2. **Visible text collection**  
   - Runs Tesseract `image_to_data`.  
   - Keeps words with confidence > 85, length 4–20, and OCR width > 30.  
   - Builds list `(text, w, conf)` for each such word.

3. **Font/size sweep**  
   For each font file and each font size from 8 to 18 pt:
   - For each visible text sample `(text, actual_width, conf)`:
     - `theoretical_width = font.getlength(text)`.
     - If positive, append `scale_factor = actual_width / theoretical_width` to a list.
   - If fewer than 5 scale factors, skip this font/size.
   - Compute mean and standard deviation of scale factors.
   - Store: font, size, avg_scale, std_dev, num_measurements, and **consistency** = `(std_dev / avg_scale) * 100` (coefficient of variation in %).

4. **Ranking**  
   Sort by **consistency** (ascending). Lower means the same scale factor fits more visible words—better font match.

5. **Recommendation**  
   Prints best font, size, scale factor, std dev, consistency, and number of measurements. Then a “VALIDATION” table: for each visible text sample (first 20), actual (OCR) width, predicted width (theoretical × avg_scale), error %, and status (Excellent / Good / Fair / Poor). Finally a “RECOMMENDATION” block with exact lines to put in `helpers/main.py` (e.g. `FONT_PATH`, font size).

## Output

- Document path and image size.
- Count of high-confidence visible text samples and a sample of them (text, width, confidence).
- Table of top 20 font/size combinations: Font, Size, Scale, Std Dev, Consistency %, Samples, Ranking.
- “DETECTED FONT” block with best font, size, scale, std dev, consistency, and short explanation.
- “VALIDATION” table comparing predicted vs actual widths for visible text.
- “RECOMMENDATION” with suggested `helpers/main.py` config (font path and size).

## Execution

```bash
python helpers/detect_font_v2.py
```

No CLI arguments. Edit `FILE_PATH` and `FONTS_DIR` as needed.

## When to Use

- When you want font detection based on **visible text** only (no redaction widths).
- When you have many high-confidence OCR words; consistency across them is a good indicator of correct font and size.
- Complements **detect_font.py** (which uses redaction widths and test names).

## See Also

- **detect_font.md** — Ranking by error vs redaction widths and test names.
- **find_font.md** — Simple font test with one control word.
- **main.md** — Where to apply the recommended font path and size (`helpers/main.py`).
