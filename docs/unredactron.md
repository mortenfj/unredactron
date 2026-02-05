# unredactron.py

## Purpose

Main entry point for the Unredactron forensic analyzer. Loads candidates from `candidates.csv`, finds redactions in the PDF, and ranks matches by width error and confidence. The original Colab-oriented engine with the `RedactionCracker` class now lives in `helpers/main.py`.

## Location

- **Path:** `unredactron.py` (project root)

The remainder of this document describes the earlier Colab-oriented engine (including `RedactionCracker`); that implementation now lives in **helpers/main.py** (see [main.md](main.md)). The current root script is the CSV-based analyzer described in README_UNREDACTRON.md.

## Dependencies (legacy / helpers/main.py)

- `cv2` (OpenCV)
- `numpy`
- `pytesseract`
- `pandas`
- `pdf2image` (`convert_from_path`)
- `PIL` (`Image`, `ImageFont`, `ImageDraw`)
- `os`
- `google.colab.drive` (Colab only; must be removed or stubbed for local runs)

## Main Components

### 1. Colab Setup (Lines 10–26)

- Runs shell commands to install `poppler-utils`, `tesseract-ocr`, and Python packages.
- Mounts Google Drive and prints instructions to upload font files (`times.ttf`, `calibri.ttf`).

**Local use:** Comment out or remove the `!` install lines, `from google.colab import drive`, and `drive.mount()`. Ensure system deps and Python packages are installed locally.

### 2. Class: `RedactionCracker`

The forensic engine used for calibration, redaction detection, and width matching.

#### `__init__(self, font_path, font_size_pt=12)`

- **Parameters:** `font_path` (str), `font_size_pt` (int, default 12).
- **Behavior:** Loads the TrueType font with PIL `ImageFont.truetype`. Raises `ValueError` if the font cannot be loaded. Leaves `px_per_pt` and `tracking_px` at 0 (reserved for future use); actual scaling is done via `scale_factor` set in `calibrate`.

#### `calibrate(self, image_cv, control_word)`

- **Parameters:** `image_cv` (BGR numpy array), `control_word` (str).
- **Behavior:**
  1. Runs Tesseract `image_to_data` on the image.
  2. Finds the first word that contains `control_word` (case-insensitive) and uses its bounding box `(x, y, w_box, h_box)`.
  3. Computes theoretical width of `control_word` with `self.font.getlength(control_word)`.
  4. Sets `self.scale_factor = real_width / base_len` (real width from OCR, base from font).
- **Returns:** `True` if the control word was found and scale was set; `False` otherwise. Prints progress and errors.

#### `find_redactions(self, image_cv)`

- **Parameters:** `image_cv` (BGR numpy array).
- **Behavior:**
  1. Converts to grayscale and applies binary threshold (10, invert) so black regions become white.
  2. Uses `cv2.findContours` (external, simple chain).
  3. Keeps contours with `w > 30`, `h > 10`, and `w/h > 1.5`.
  4. Sorts by vertical position (reading order).
- **Returns:** List of `(x, y, w, h)` bounding boxes.

#### `check_width_match(self, name, target_width_px, tolerance=2.0)`

- **Parameters:** `name` (str), `target_width_px` (float), `tolerance` (float, default 2.0).
- **Behavior:** Computes `base_width = self.font.getlength(name)`, then `predicted_width = base_width * self.scale_factor`. Compares to `target_width_px`.
- **Returns:** `(True, predicted_width)` if `abs(predicted_width - target_width_px) <= tolerance`, else `(False, predicted_width)`.

#### `artifact_check(self, name, image_cv, box_coords)`

- **Parameters:** `name`, `image_cv`, `box_coords` (x, y, w, h).
- **Behavior:** Extracts a small ROI around the box. Placeholder only; returns the string `"Not Implemented in Basic Mode"`. Intended for future artifact/anti-aliasing checks.

### 3. Configuration (Lines 134–141)

Hardcoded for Colab/Drive:

- **FILE_PATH:** PDF or image path (e.g. Drive path to `EFTA00513855.pdf`).
- **FONT_PATH:** Path to TrueType font (e.g. `times.ttf`).
- **CONTROL_WORD:** Word used for calibration (e.g. `"Subject"`).
- **SUSPECT_LIST:** List of names to test (e.g. Sarah Kellen, Ghislaine Maxwell, etc.).

### 4. Function: `run_investigation()`

- Loads the document: if `FILE_PATH` ends in `.pdf`, converts with `convert_from_path` and uses `pages[0]`; otherwise reads with `cv2.imread`. Converts to BGR.
- Instantiates `RedactionCracker(FONT_PATH, font_size_pt=12)`.
- Calls `calibrate(img, CONTROL_WORD)`; exits if calibration fails.
- Calls `find_redactions(img)` and prints the number of blocks.
- For each redaction box, tests every name in `SUSPECT_LIST` with variations `[name, name.upper()]`, using `check_width_match(..., tolerance=3.0)`.
- Prints “POTENTIAL HITS” for each block that has at least one match, with predicted width.

### 5. Entry Point

- Calls `run_investigation()` when the script is run (e.g. in Colab).

## Execution

- **Current root script (CSV-based):** `uv run unredactron.py` — uses `candidates.csv`, no Colab.
- **Colab-style engine:** `python helpers/main.py` — see [main.md](main.md). For Colab: upload fonts, set paths in config; for local: set `FILE_PATH`, `FONT_PATH`, etc. at top of `helpers/main.py`.

## Output

- Console output: calibration status, number of redactions, and for each block either “POTENTIAL HITS” with matching names and predicted widths, or “(No geometric matches found)”.

## Differences from helpers/main.py

- Colab-specific setup and Drive paths (in the legacy version).
- Single-page analysis (`pages[0]` only) in the legacy version.
- Tolerance 3.0 px in legacy; no per-page or aggregate match summary.
- No CSV or structured output in legacy; results are print-only.

## See Also

- **README_UNREDACTRON.md** — Usage for the current CSV-based root script.
- **main.md** — `helpers/main.py`: local, multi-page Colab-style engine with configurable tolerance and match summary.
- **docs/CLAUDE.md** — Project architecture and configuration reference.
