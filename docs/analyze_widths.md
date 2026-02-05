# analyze_widths.py

## Purpose

Aggregates **all redaction widths** across **all pages** of a PDF, clusters them (e.g. by rounding to nearest 5 px), suggests possible content types (short/medium/long name, phrase, etc.), and tests suspect names against the most common widths with a relaxed tolerance. Helps see patterns and which names fit which width buckets.

## Location

- **Path:** `helpers/analyze_widths.py`

## Dependencies

- `cv2`, `numpy`, `pdf2image`, `collections.Counter`
- **PIL.ImageFont**, **pytesseract** (used later for calibration and name testing)

## Configuration (Top of File)

| Variable | Meaning | Default |
|----------|---------|---------|
| `FILE_PATH` | Target PDF | `"files/EFTA00513855.pdf"` |

Calibration and name list are hardcoded in the script: control word `"Contacts"`, font `fonts/fonts/times.ttf` at 12 pt, and `SUSPECT_NAMES` (e.g. Sarah Kellen, Ghislaine Maxwell, …).

## Algorithm

1. **Load PDF and collect redactions**  
   Same `find_redactions(image_cv)` logic as elsewhere: grayscale, threshold 10 inverted, contours, filter (w>30, h>10, w/h>1.5). For each redaction on each page, append width to `all_widths` and `(page, x, y, w, h)` to `all_redactions`.

2. **Width clusters (5 px buckets)**  
   For each width, `cluster_key = round(w/5)*5`. Count per cluster. For each cluster, assign a “Possible Content” label by width:
   - &lt; 80: “Short (initials, dates, numbers)”
   - &lt; 150: “Medium (short names, single words)”
   - &lt; 250: “Name (First Last)”
   - &lt; 350: “Long name / Uppercase name”
   - &lt; 500: “Multiple names / phrases”
   - ≥ 500: “Very long (addresses, paragraphs)”

3. **Print cluster table**  
   Sorted by cluster key: width range, count, percentage, possible content.

4. **Top 10 exact widths**  
   `Counter(all_widths)`; print the 10 most common exact widths and their counts/percentages.

5. **Test suspect names**  
   - Calibrate on first page: Tesseract find “Contacts”, get OCR width; `scale_factor = control_width_px / font.getlength("Contacts")` with Times 12 pt.
   - For each of the top 10 most common widths, test each suspect name in original and uppercase. Predicted = `font.getlength(variant) * scale_factor`. Match if `abs(predicted - redaction_width) <= 15`.
   - For each width: either list matches (name, predicted, diff) or “No matches within 15px” with closest name and diff.

## Output

- “Loading …”, “Loaded N pages”, total redaction count.
- “REDACTION WIDTH CLUSTERS”: table Width Range, Count, Percentage, Possible Content.
- “TOP 10 MOST COMMON EXACT WIDTHS”: width, count, percentage.
- “TESTING SUSPECT NAMES AGAINST MOST COMMON WIDTHS”: for each of the top 10 widths, either matching names with predicted/diff or closest name and diff.

## Execution

```bash
python helpers/analyze_widths.py
```

Edit `FILE_PATH` and, inside the script, the control word, font path, and `SUSPECT_NAMES` if needed.

## Use Case

- Understand distribution of redaction sizes (many short vs many long).
- See which names geometrically fit the most frequent widths (with 15 px tolerance).
- Choose candidate names or width buckets for deeper analysis in **main.py** or **pattern_match.py**.

## See Also

- **find_redactions.md** — Lists redactions per page (no clustering or name test).
- **main.md** — Full pipeline with per-redaction matching and frequency summary.
- **debug_matches.md** — Per-block predicted vs actual width for all names.
