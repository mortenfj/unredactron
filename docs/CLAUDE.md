# CLAUDE.md (Project Guidance)

## Purpose

**CLAUDE.md** is a project guidance file for AI assistants (e.g. Claude Code) working in this repository. It is **not** a script; it lives in the project root and is referenced by the editor. It summarizes the Unredactron architecture, configuration, font library, implementation details, limitations, and testing approach so that code changes stay consistent with the design.

## Location

- **Path:** `CLAUDE.md` (project root). A copy or summary of its content is also documented here in `docs/CLAUDE.md` for the docs index.

## Contents (Summary)

### Project Overview

- Unredactron is a digital forensic tool that tries to identify redacted text via:
  1. **Calibration** — Visible “control word” → DPI/scaling.
  2. **Detection** — Black redaction bars with OpenCV contours.
  3. **Matching** — Predicted pixel width of suspect names vs redaction widths.
  4. **Verification** — Placeholder for anti-aliasing artifact checks.

- Framed as security research/forensics for documents where redactions may have been applied incorrectly.

### Running the Scripts

**IMPORTANT - Always use uv for this project:**

- **Dependency installation:** `uv pip install <package>` (never use `pip install` directly)
- **Script execution:** `uv run python <script>.py` (never use `python <script>.py` directly)

**Examples:**
```bash
# Install dependencies
uv pip install pdf2image pytesseract opencv-python-headless pandas Pillow

# Run scripts
uv run python unredactron.py
uv run python helpers/forensic_halo.py
uv run python helpers/unredactron_forensic.py --file files/document.pdf --font fonts/fonts/times.ttf
```

**Available scripts:**
- **Main analyzer (root):** `uv run python unredactron.py` — CSV-based, uses `candidates.csv`; no Colab.
- **Colab-style pipeline:** `uv run python helpers/main.py` — uses `RedactionCracker`, hardcoded FILE_PATH, FONT_PATH, CONTROL_WORD, SUSPECT_LIST. Designed for Colab; for local use set config at top of `helpers/main.py`.
- **Forensic halo extraction:** `uv run python helpers/forensic_halo.py` — Advanced artifact detection with corner exclusion and diagnostic sheets.
- **Integrated forensic analysis:** `uv run python helpers/unredactron_forensic.py` — Combines width matching with artifact detection.
- Prerequisites: `poppler-utils`, `tesseract-ocr`; Python: `pdf2image`, `pytesseract`, `opencv-python-headless`, `pandas`, `Pillow`.

### Architecture

- **Core class:** `RedactionCracker` (in `helpers/main.py`).
  - **__init__:** Load font, set calibration vars.
  - **calibrate:** OCR control word → scale factor.
  - **find_redactions:** Threshold + contours → filtered boxes.
  - **check_width_match:** Predicted width vs target within tolerance.
  - **artifact_check:** Placeholder.

- **Configuration:** FILE_PATH, FONT_PATH, CONTROL_WORD, SUSPECT_LIST (hardcoded).
- **Main flow (helpers/main.py):** Load doc → init engine → calibrate → find redactions → test each block with suspect names → report matches.
- **Root unredactron.py:** Load PDF, find redactions, load candidates from CSV, match widths, rank by error + confidence; no Tesseract calibration.

### Font Library

- Lists fonts in `fonts/fonts/` (e.g. times.ttf, arial.ttf, calibri.ttf, cour.ttf, cambria*, CENTURY.TTF, GARA.TTF). Stresses that font must match the document.

### Implementation Details

- OCR calibration: control word must be found by Tesseract; suggests trying multiple words or manual check.
- Tolerance: default 3 px in Colab script; 15 px in `helpers/main.py`; lower = fewer false positives.
- Name variations: currently name and name.upper(); suggests adding “Last, First”, initials, misspellings.
- Artifact detection: not implemented; placeholder for anti-aliasing/template logic.

### Known Limitations

- Single font; first page only in original script; no automated font detection; basic single-word calibration; 12 pt assumed.

### Testing

- No automated tests. Manual steps: test PDF with known redactions, verify control word, check scale factor and redaction count, validate width matching.

## Use Case

- Read by AI assistants and developers to understand the project before editing code or adding features.
- Keeps architecture and config in one place; docs in `docs/` reference it for run instructions and prerequisites.

## See Also

- **docs/README.md** — Documentation index and typical workflow.
- **docs/unredactron.md** — Root CSV-based analyzer.
- **docs/main.md** — `helpers/main.py`: RedactionCracker and Colab-style config.
- **docs/what_we_tried_to_do.md** — Methodology narrative (calibration, tracking, artifacts).
- **helpers/CLAUDE.md** — Additional guidance for helper scripts.
