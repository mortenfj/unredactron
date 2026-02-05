# find_redactions.py

## Purpose

Scans **all pages** of a PDF for black redaction bars using the same OpenCV contour logic as the main engine. Prints per-page counts and positions/sizes of each block, plus a short summary and list of recommended pages to analyze further.

## Location

- **Path:** `helpers/find_redactions.py`

## Dependencies

- `cv2`, `numpy`, `pdf2image` (no Tesseract or PIL fonts)

## Configuration

| Variable | Meaning | Default |
|----------|---------|---------|
| `FILE_PATH` | Target PDF path | `"files/EFTA00513855.pdf"` |

## Function: `find_redactions(image_cv)`

- **Parameter:** `image_cv` — BGR image (numpy array).
- **Behavior:**
  1. Grayscale, binary threshold 10 (inverted) so black regions become white.
  2. `cv2.findContours` (external, simple chain).
  3. For each contour: bounding rect `(x, y, w, h)`; keep if `w > 30`, `h > 10`, and `w/h > 1.5`.
  4. Sort by y (reading order).
- **Returns:** List of `(x, y, w, h)` tuples.

## Main Script Flow

1. Load PDF with `convert_from_path(FILE_PATH)`.
2. For each page: convert to BGR, call `find_redactions(img_bgr)`.
3. For pages with at least one redaction:
   - Append `(page_number, redactions)` to `pages_with_redactions`.
   - Print page number, count of redactions, and for each block: index, position `(x,y)`, size `w×h` in pixels.
4. For pages with no redactions, print “No redactions”.
5. Print summary: how many pages have redactions, then “Recommended pages to analyze” with page numbers and block counts.

## Output

- “Loading …” and “Loaded N pages”.
- Per page with redactions: “Page NN: M redaction(s) found” and lines “Block J: pos=(x,y), size=w×h px”.
- Per page without: “Page NN: No redactions”.
- “Summary: K pages have redactions” and “Recommended pages to analyze” list.

## Execution

```bash
python helpers/find_redactions.py
```

No CLI arguments. Edit `FILE_PATH` as needed.

## Use Case

- Quick inventory of where redactions are before running calibration and width matching.
- Choosing which pages to focus on in **main.py** or other scripts.
- Verifying that the contour/threshold logic finds the expected bars on your PDF.

## See Also

- **main.md** — Uses the same redaction logic and then runs width matching.
- **analyze_widths.md** — Aggregates widths across pages and clusters by size.
- **detect_artifacts.md** — Uses redaction boxes to extract artifact regions.
