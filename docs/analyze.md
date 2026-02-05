# analyze.py

## Purpose

Runs a **complete redaction analysis** in one script: (1) auto-detect font (Times New Roman only, best size by consistency over visible text), (2) find redactions on the first page, (3) test all suspect names with 15 px tolerance, (4) report matches grouped by width and a match frequency table.

## Location

- **Path:** `helpers/analyze.py`

## Dependencies

- `cv2`, `numpy`, `pytesseract`, `pdf2image`, `PIL.ImageFont`, `os`

## Configuration (Top of File)

| Variable | Meaning | Default |
|----------|---------|---------|
| `FILE_PATH` | Target PDF | `"files/EFTA00037366.pdf"` |
| `FONTS_DIR` | Font directory (only Times used) | `"fonts/fonts/"` |
| `SUSPECT_LIST` | Names to test | e.g. Sarah Kellen, Ghislaine Maxwell, … |

## Algorithm

### STEP 1: Auto-detect font (Times only)

- Load first page to BGR. Run Tesseract `image_to_data`.
- Collect visible text: confidence > 85, length 4–20, width > 30. Store `(text, w)`.
- Sweep font sizes 8–14 for **times.ttf** only:
  - For each (text, actual_width): `scale_factor = actual_width / font.getlength(text)`.
  - Require at least 5 scale factors. Compute mean and std; consistency = (std/mean)×100.
  - Keep size with lowest consistency; store `best_size`, `best_scale`, `best_consistency`.
- Print detected font (Times), size, scale factor, consistency.

### STEP 2: Find redactions

- Grayscale, threshold 10 inverted, contours, filter (w>30, h>10, w/h>1.5). Count and print.

### STEP 3: Test suspect names

- Load Times at `best_size`. For each redaction (x,y,w,h) and each name in SUSPECT_LIST, variants [name, name.upper()]:
  - `predicted = font.getlength(variant) * best_scale`, `diff = abs(predicted - w)`.
  - If diff ≤ 15: append dict with x, y, w, h, name variant, predicted, diff to `matches`.

### STEP 4: Results

- If matches: group by width; for each width print count and unique names; for single-name widths print “Best” match (lowest diff). Then “MATCH FREQUENCY” table: name → occurrence count.
- If no matches: print “No matches found within 15px tolerance”.

## Output

- “COMPLETE REDACTION ANALYSIS” header.
- STEP 1: Detected font (Times), size, scale, consistency.
- STEP 2: Number of redaction blocks.
- STEP 3: “Testing N suspect names…”.
- “RESULTS”: total match count; table of redaction width vs names and best match; “MATCH FREQUENCY” by name.

## Execution

```bash
python helpers/analyze.py
```

Edit `FILE_PATH`, `FONTS_DIR`, and `SUSPECT_LIST` as needed. Only first page is analyzed; font is Times only.

## Use Case

- Single script to go from PDF to match list without manually setting control word or font (assumes Times is correct).
- Quick “full pipeline” run on one document and one page.

## See Also

- **detect_font_v2.md** — Full font/size detection over all fonts and visible text.
- **main.md** — Multi-page pipeline with explicit control word and font path.
- **analyze_widths.md** — Width clustering and name test against top widths.
