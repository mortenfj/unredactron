# debug_matches.py

## Purpose

**Debug script** to compare **predicted** pixel widths (from font + calibration) to **actual** redaction widths for each block and each suspect name. Prints a table per redaction block with predicted width, actual width, difference, and MATCH status (within 3 px), plus the “closest” name per block. Useful to tune tolerance and see how well the font/scale fit the document.

## Location

- **Path:** `helpers/debug_matches.py`

## Dependencies

- `cv2`, `numpy`, `pytesseract`, `pdf2image`, `PIL` (`ImageFont`, `ImageDraw`, `Image`)

## Configuration (Top of File)

| Variable | Meaning | Default |
|----------|---------|---------|
| `FILE_PATH` | Target PDF | `"files/EFTA00513855.pdf"` |
| `FONT_PATH` | TrueType font | `"fonts/fonts/times.ttf"` |
| `CONTROL_WORD` | Word used for calibration | `"Contacts"` |
| `SUSPECT_LIST` | Names to test | e.g. Sarah Kellen, Ghislaine Maxwell, … |

## Algorithm

1. **Load and calibrate**  
   First page to BGR. Tesseract finds first word containing `CONTROL_WORD` (case-insensitive); `real_width` = OCR box width. Load font at 12 pt. `base_len = font.getlength(CONTROL_WORD)`, `scale_factor = real_width / base_len`. Print calibration: control word, actual OCR width, theoretical font width, scale factor.

2. **Find redactions**  
   Same logic as main engine: grayscale, threshold 10 inverted, contours, filter (w>30, h>10, w/h>1.5), sort by y. Print count of redaction blocks on page 1.

3. **Per-block analysis**  
   For each redaction `(x, y, w, h)`:
   - Print block index and width.
   - For each name in SUSPECT_LIST, variants [name, name.upper()]:
     - `base_width = font.getlength(variant)`, `predicted_width = base_width * scale_factor`, `diff = abs(predicted_width - w)`.
     - Track closest (variant, predicted_width) by minimum diff.
     - Print: variant, predicted width, actual width (w), diff, and “MATCH” if diff ≤ 3.0 else “+X.Xpx”.
   - Print “Closest: ‘name’ at X.Xpx (diff: ±X.Xpx)”.

## Output

- “WIDTH ANALYSIS - Predicted vs Actual” header.
- Calibration block: control word, actual OCR width, theoretical font width, scale factor.
- “Found N redaction blocks on page 1”.
- “ANALYZING EACH REDACTION BLOCK”: for each block, table “Name | Predicted | Actual | Diff | Status” and “Closest” line.

## Execution

```bash
python helpers/debug_matches.py
```

Edit `FILE_PATH`, `FONT_PATH`, `CONTROL_WORD`, and `SUSPECT_LIST` as needed. No CLI arguments.

## Use Case

- See exactly how far each name is from each redaction width (in pixels).
- Decide whether to relax or tighten tolerance (e.g. 3 px vs 15 px in helpers/main.py).
- Check if calibration or font is off (systematic over/under prediction).

## See Also

- **main.md** — Uses 15 px tolerance; this script uses 3 px for MATCH.
- **find_font_size.md** — Sweeps font size; this script fixes 12 pt.
- **analyze_widths.md** — Tests names against top widths; this script tests every block.
