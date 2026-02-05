# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Unredactron is a digital forensic tool that attempts to identify redacted text in PDF documents through geometric and typographic analysis. The core technique:

1. **Calibration**: Uses a visible "control word" to determine the document's exact DPI/scaling factor
2. **Detection**: Finds black redaction bars using OpenCV contour detection
3. **Matching**: Calculates the expected pixel width of suspect names and compares against redaction block widths
4. **Verification**: (Placeholder) Checks for anti-aliasing artifacts at redaction edges

**Important**: This is a security research/forensics tool designed for analyzing documents where redactions may have been applied incorrectly.

## Running the Script

This script is designed for **Google Colab** but can run locally with modifications.

### Prerequisites

```bash
# System dependencies
apt-get install poppler-utils tesseract-ocr

# Python dependencies - ALWAYS use uv
uv pip install pdf2image pytesseract opencv-python-headless pandas Pillow
```

**IMPORTANT**: This project uses `uv` as the Python package manager. Always use `uv pip install` instead of `pip install` for dependency management to ensure consistent environments and faster resolution.

### Execution

**ALWAYS use `uv run` for executing Python scripts**:

```bash
# Run the main script
uv run python unredactron.py

# Run helper scripts
uv run python helpers/forensic_halo.py
uv run python helpers/detect_artifacts.py

# Run with arguments
uv run python helpers/unredactron_forensic.py --file files/document.pdf --font fonts/fonts/times.ttf --csv candidates.csv
```

Using `uv run` ensures the script executes with the correct Python environment and dependencies managed by uv.

For local execution (not Colab), comment out/remove the Google Drive mounting code:
- Lines 21-24: `from google.colab import drive` and `drive.mount()`
- Update paths in configuration section (lines 134-141)

## Architecture

### Core Class: `RedactionCracker`

Located entirely in `unredactron.py`, this class implements the forensic engine:

**Initialization** (`__init__`):
- Loads a TrueType font matching the target document
- Sets up calibration variables (`scale_factor`)

**Calibration** (`calibrate`):
- Takes an image and a known visible word (e.g., "Subject")
- Uses OCR (`pytesseract`) to find the word's bounding box
- Calculates `scale_factor = real_pixel_width / theoretical_font_width`
- This accounts for DPI, rendering differences, and font tracking

**Redaction Detection** (`find_redactions`):
- Converts image to grayscale and applies binary threshold
- Uses OpenCV `findContours` to locate black rectangles
- Filters by size/aspect ratio (width > 30px, height > 10px, width/height > 1.5)
- Returns sorted list of `(x, y, w, h)` bounding boxes

**Width Matching** (`check_width_match`):
- Renders a suspect name using the calibrated font
- Applies `scale_factor` to predict pixel width
- Returns match if within `tolerance` pixels (default 2.0px)

### Configuration Section (lines 134-141)

Hardcoded parameters that must be updated for each analysis:
- `FILE_PATH`: Target PDF/image path
- `FONT_PATH`: Path to matching TrueType font (critical for accuracy)
- `CONTROL_WORD`: A visible word on the page for calibration
- `SUSPECT_LIST`: Array of names to test against redactions

### Main Investigation Flow (`run_investigation`)

1. Loads first page of PDF (or image directly)
2. Initializes `RedactionCracker` with specified font
3. Calibrates using control word
4. Finds all redaction blocks
5. For each block, tests all suspect names and variations (original, uppercase)
6. Reports matches where predicted width matches block width within tolerance

## Font Library

Available fonts in `fonts/fonts/`:
- `times.ttf` - Times New Roman (most common for legal documents)
- `arial.ttf` - Arial
- `calibri.ttf` - Calibri
- `cour.ttf` - Courier (monospaced)
- `cambria*.ttf` - Cambria variants
- `CENTURY.TTF`, `GARA.TTF` - Additional fonts

**Critical**: The font must match the document's original font. Mismatched fonts will produce incorrect width calculations.

## Key Implementation Details

### OCR Calibration Strategy
The script assumes the control word is found perfectly by Tesseract. In practice, you may need to:
- Try multiple control words if OCR fails
- Adjust Tesseract configuration (currently using defaults)
- Manually verify the detected bounding box

### Tolerance Settings
- Default tolerance: 3.0 pixels (line 179)
- Lower values = fewer false positives, more false negatives
- Adjust based on document quality and redaction precision

### Name Variations
Currently tests: `[name, name.upper()]`

You may want to add:
- "Last, First" format
- Initials (e.g., "J. Smith")
- Common misspellings

### Artifact Detection (Not Implemented)
The `artifact_check()` method (lines 116-130) is a placeholder for advanced verification:
- Would check for anti-aliasing pixels protruding from redaction edges
- Could use template matching to align letter shapes with artifacts
- Requires significantly more complex computer vision logic

## Known Limitations

1. **Single font assumption**: Cannot handle documents with mixed fonts
2. **First page only**: Currently analyzes `pages[0]` only (line 147)
3. **No automated font detection**: User must manually specify the correct font
4. **Basic calibration**: Uses single control word; multi-word calibration could improve accuracy
5. **No size variance**: Assumes 12pt font throughout (hardcoded in initialization)

## Testing

There are no automated tests. To test modifications:
1. Prepare a test PDF with known redacted content
2. Verify the control word is detected via OCR
3. Check that `scale_factor` is reasonable (typically 4.0-8.0 for standard DPIs)
4. Confirm redaction blocks are detected (check count and dimensions)
5. Validate width matching produces expected results
