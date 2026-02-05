# main.py

## Purpose

Local entry point for Unredactron. Runs the full forensic pipeline across **all pages** of a PDF (or a single image), reports geometric matches between suspect names and redaction block widths, and prints a summary with match frequency by name.

## Location

- **Path:** `helpers/main.py`

## Dependencies

- `cv2`, `numpy`, `pytesseract`, `pdf2image`, `PIL` (`Image`, `ImageFont`, `ImageDraw`), `os`
- **Note:** No `pandas` usage in the main flow; no Google Colab code.

## Configuration (Lines 119–129)

Editable at the top of the file:

| Variable | Meaning | Example |
|----------|---------|---------|
| `FILE_PATH` | Target PDF or image path | `"files/EFTA00037366.pdf"` |
| `FONT_PATH` | TrueType font file (must match document font) | `"fonts/fonts/times.ttf"` |
| `CONTROL_WORD` | Visible word used for calibration | `"Subject:"` |
| `SUSPECT_LIST` | List of names to test against redactions | List of strings (e.g. Sarah Kellen, Ghislaine Maxwell, …) |

## Main Flow: `run_investigation()`

1. **Validation and logging**  
   Prints configuration: target file, font, control word, number of suspects.

2. **Load document**  
   - If `FILE_PATH` ends in `.pdf`: uses `convert_from_path` (default DPI), converts first page to BGR for calibration.  
   - Else: loads image with `cv2.imread` and wraps in a single-page list.

3. **Initialize engine**  
   Builds BGR image from `pages[0]`, creates `RedactionCracker(FONT_PATH, font_size_pt=12)`. Exits with error if font load fails.

4. **Calibrate**  
   Calls `engine.calibrate(img, CONTROL_WORD)`. If it returns `False`, prints that calibration failed and returns.

5. **Scan all pages**  
   For each page:
   - Converts page to BGR.
   - Calls `engine.find_redactions(img)`.
   - For each redaction box `(x, y, w, h)`:
     - For each name in `SUSPECT_LIST`, tests variants `[name, name.upper()]`.
     - Uses `engine.check_width_match(variant, w, tolerance=15.0)`.
     - If match: appends `(page_num, x, y, w, h, variant, pred_w)` to `all_matches` and prints a line like  
       `[P{page_num}] {w}px redaction: '{variant}' (pred: {pred_w:.1f}px, diff: {diff:+.1f}px)`.

6. **Summary**  
   - If there are matches: prints total count and “Match frequency” (count per name, sorted by count descending).  
   - If none: prints “No matches found”.

## RedactionCracker Usage

`helpers/main.py` defines and uses the `RedactionCracker` class (Colab-style engine):

- **Calibration:** One control word on the first page sets `scale_factor` for all pages.
- **Tolerance:** Fixed at **15.0** pixels in `check_width_match` (more permissive than the 3.0 in `unredactron.py`).

## Execution

```bash
python helpers/main.py
```

Ensure `FILE_PATH`, `FONT_PATH`, and `CONTROL_WORD` are set for your environment and that the control word appears on the first page and is detectable by Tesseract.

## Output

- **Per-page:** For each page that has redactions, one line per matching redaction: page, width, variant name, predicted width, and difference.
- **Summary:** Total number of potential matches and a “Match frequency” table of name → occurrence count.

## Differences from unredactron.py (root)

- Root `unredactron.py` uses CSV candidates and a different pipeline (no Tesseract calibration). This script (`helpers/main.py`) uses hardcoded SUSPECT_LIST and `RedactionCracker`.
- No Colab or Drive; local paths only.
- Processes **all pages** of the PDF.
- **Tolerance 15 px** (vs 3 px in older Colab script).
- Match frequency summary and clearer section headers.
- More verbose configuration and step logging.

## See Also

- **unredactron.py** (root) — CSV-based analyzer; run with `uv run unredactron.py`.
- **helpers/detect_font.py** / **helpers/detect_font_v2.py** — To choose `FONT_PATH` and font size.
- **helpers/find_redactions.py** — To see where redactions are before running the full pipeline.
- **docs/CLAUDE.md** — Project overview and configuration.
