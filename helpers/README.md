# Helper Scripts Archive

This folder contains development, testing, and analysis scripts that were used during the development of Unredactron. These are kept for reference but are not needed for normal operation.

## Categories

### Main Analysis Scripts (Used for Final Results)

- **enhanced_brute_force.py** - Enhanced CSV-weighted brute force analysis (974 variants)
- **brute_force_csv.py** - True brute force testing 351 names from names.csv
- **top10_detections.py** - Generate top 10 detection list
- **top10_summary.py** - Summary of top detections
- **verify_marcinkova.py** - Verify Marcinkova width match
- **verify_anne_marie.py** - Verify Anne Marie width match

### Font Detection Scripts

- **detect_font.py** - Auto-detect document font
- **detect_font_v2.py** - Improved font detection algorithm
- **find_font.py** - Find font in document
- **find_font_size.py** - Detect font size

### Artifact Detection Scripts

- **detect_artifacts.py** - Detect anti-aliasing artifacts
- **analyze_artifacts.py** - Analyze artifact patterns
- **anti_aliasing_detect.py** - Detect anti-aliasing at edges
- **specific_protrusions.py** - Detect protrusions excluding corners
- **subtract_analysis.py** - Artifact detection by subtraction method
- **pixel_edges.py** - Analyze pixel-level edge details
- **protrusion_detect.py** - Detect letter protrusions at redaction edges

### Kellen Analysis Scripts

- **find_kellen.py** - Find "Kellen" redactions
- **kellen_confirm.py** - Three-pillar confirmation of "Kellen"
- **search_brunel.py** - Search for "Brunel" in document

### Brunel/Attempts Analysis Scripts

- **find_attempts_brunel.py** - Find "Attempts were made to [NAME] and Brunel"
- **deduce_brunel.py** - Deduce name in "Attempts...Brunel" sentence
- **analyze_attempts_brunel.py** - Full three-pillar analysis
- **double_name_analysis.py** - Test double-name combinations
- **brute_force_brunel.py** - Brute force with letter bounds

### Search/Find Scripts

- **find_between.py** - Find redactions between two words
- **find_redactions.py** - Find all redactions in document
- **search_brunel.py** - Search for Brunel text

### Visualization Scripts

- **visualize_context.py** - Visualize redactions with context arrows
- **visual_compare.py** - Compare multiple visualizations
- **show_all_pixels.py** - Show all pixel values

### Analysis/Debugging Scripts

- **analyze.py** - General analysis script
- **analyze_widths.py** - Width analysis
- **detailed_match.py** - Detailed matching analysis
- **debug_matches.py** - Debug matching issues
- **debug_ocr.py** - Debug OCR output
- **pattern_match.py** - Pattern matching

### Reconstruction Scripts

- **reconstruct.py** - Reconstruct redacted text
- **reconstruct_from_protrusions.py** - Reconstruct from protrusions
- **letter_reconstruction.py** - Individual letter reconstruction

### Development Scripts

- **main.py** - Original main script (superseded by unredactron.py)
- **analyze_brunel.py** - Early Brunel analysis attempt

### Data Files

- **names.csv** - Original malformed CSV with all names and confidence markers
- **names_clean.txt** - Cleaned list of 351 unique names
- **CLAUDE.md** - Project documentation for Claude AI

## Script Usage

These scripts are primarily for reference and debugging. To use them:

```bash
cd helpers
uv run script_name.py
```

## Note

Most of these scripts were created incrementally during development and may reference older file paths or dependencies. The main `unredactron.py` script in the parent directory is the production-ready version.
