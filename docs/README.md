# Unredactron Documentation

This directory contains detailed documentation for each file in the Unredactron project—a digital forensic tool for analyzing redacted PDF documents through geometric and typographic analysis.

## Project Overview

Unredactron attempts to identify redacted text by:

1. **Calibration** — Using a visible "control word" to determine document DPI/scaling
2. **Detection** — Finding black redaction bars with OpenCV contour detection
3. **Matching** — Comparing predicted pixel widths of suspect names to redaction block widths
4. **Verification** — (Partial) Checking for anti-aliasing artifacts at redaction edges

## Documentation Index

### Core Engine & Entry Points

| File | Description |
|------|-------------|
| [unredactron.md](unredactron.md) | Main CSV-based analyzer at project root (`unredactron.py`); run with `uv run unredactron.py` |
| [main.md](main.md) | Colab-style pipeline in `helpers/main.py`: `RedactionCracker`, full multi-page investigation with summary and match frequency |

### Font Detection & Sizing

| File | Description |
|------|-------------|
| [detect_font.md](detect_font.md) | Automatic font detection: tests all fonts at multiple sizes, ranks by average error vs redaction widths |
| [detect_font_v2.md](detect_font_v2.md) | Font detection via visible text: compares OCR measurements to theoretical font widths for consistency |
| [find_font.md](find_font.md) | Font finder: tests fonts against a fixed control word and sample redaction widths |
| [find_font_size.md](find_font_size.md) | Font size sweep: finds best point size for a given font using control word calibration |

### Redaction & Artifact Analysis

| File | Description |
|------|-------------|
| [find_redactions.md](find_redactions.md) | Redaction scanner: finds and lists black bars across all PDF pages |
| [detect_artifacts.md](detect_artifacts.md) | Artifact detection: high-DPI analysis of "halo" regions around redactions for text traces |
| [analyze_artifacts.md](analyze_artifacts.md) | Visual artifact analysis: inspects saved artifact images (halo brightness, pixel distribution) |
| [analyze_widths.md](analyze_widths.md) | Width clustering: groups redaction widths, suggests content type, tests suspect names |
| [analyze.md](analyze.md) | Complete analysis: auto-detect font (Times), find redactions, test suspect names, report matches |
| [pattern_match.md](pattern_match.md) | Pattern matching: compares rendered suspect name edges to artifact edges at 600 DPI |

### Reconstruction & Comparison

| File | Description |
|------|-------------|
| [detailed_match.md](detailed_match.md) | Deep analysis of one high-confidence match: edge regions, similarity %, visual comparison and difference map |
| [visual_compare.md](visual_compare.md) | Visual comparison: actual artifact vs expected pattern for one candidate; saves numbered images to `comparisons/` |
| [letter_reconstruction.md](letter_reconstruction.md) | Letter-by-letter reconstruction: letter signatures, slot analysis, best letter per position; outputs to `letter_analysis/` |
| [reconstruct.md](reconstruct.md) | Forensic reconstruction: score dictionary words and names against artifact features (width, ascenders/descenders, edges) |

### Debug & Utilities

| File | Description |
|------|-------------|
| [debug_ocr.md](debug_ocr.md) | OCR debug: prints all Tesseract-detected text with confidence and bounding boxes |
| [debug_matches.md](debug_matches.md) | Width match debug: predicted vs actual width for each redaction and suspect name |

### Project Metadata

| File | Description |
|------|-------------|
| [CLAUDE.md](CLAUDE.md) | Guidance for AI assistants (architecture, config, limitations); see also `helpers/CLAUDE.md` |
| [what_we_tried_to_do.md](what_we_tried_to_do.md) | Methodology notes: calibration, tracking, redaction detection, brute-force, artifact verification |

Scripts in the tables above (except `unredactron.py`) live in **helpers/** and are run from the project root, e.g. `python helpers/find_redactions.py`.

## Code Layout

- **Project root:** `unredactron.py` — main CSV-based analyzer (`uv run unredactron.py`).
- **helpers/** — Helper scripts for font detection, redaction scanning, artifact analysis, reconstruction, and the original Colab-style pipeline (`RedactionCracker` in `helpers/main.py`). Run from project root, e.g. `python helpers/main.py`.

## Typical Workflow

1. **Inspect document** — `python helpers/find_redactions.py` to see where redactions are; `python helpers/debug_ocr.py` to pick a control word.
2. **Choose font** — `python helpers/detect_font.py` or `python helpers/detect_font_v2.py` to recommend font/size; optionally `find_font.py`, `find_font_size.py` in `helpers/`.
3. **Run investigation** — `uv run unredactron.py` (CSV candidates) or `python helpers/main.py` (hardcoded `FILE_PATH`, `FONT_PATH`, `CONTROL_WORD`, `SUSPECT_LIST`).
4. **Analyze patterns** — `python helpers/analyze_widths.py` for width clusters; `python helpers/analyze.py` for full pipeline with auto font.
5. **Artifacts (optional)** — `python helpers/detect_artifacts.py` to generate artifact images; `analyze_artifacts.py` and `pattern_match.py` in `helpers/` to analyze them.
6. **Deep-dive on one match** — `python helpers/pattern_match.py` → take a strong match; `python helpers/visual_compare.py` for side-by-side images in `comparisons/`; `python helpers/detailed_match.py` for scoring and difference map in `detailed_analysis/`.
7. **Reconstruction (optional)** — `python helpers/letter_reconstruction.py` for letter-slot analysis (outputs in `letter_analysis/`); `python helpers/reconstruct.py` for candidate-word/name scoring.
8. **Debug** — `python helpers/debug_matches.py` to see predicted vs actual widths per block.

## Output Directories

Scripts in `helpers/` that write images create or use these folders (relative to project root):

- **artifacts/** — `helpers/detect_artifacts.py`: enhanced halo images per redaction.
- **comparisons/** — `helpers/visual_compare.py`: actual vs expected artifact and edge images (01–07).
- **detailed_analysis/** — `helpers/detailed_match.py`: comparison.png, difference_map.png for one match.
- **letter_analysis/** — `helpers/letter_reconstruction.py`: per-redaction analysis images (redaction_1_analysis.png, …).
- **reconstruction/** — `helpers/reconstruct.py`: directory created; script currently prints results to console only.

## Dependencies

- **System:** `poppler-utils`, `tesseract-ocr`
- **Python:** `pdf2image`, `pytesseract`, `opencv-python-headless`, `pandas`, `Pillow`

See [CLAUDE.md](CLAUDE.md) for full prerequisites and run instructions.
