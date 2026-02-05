# Changelog

All notable changes to Unredactron will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Dynamic tolerance system for width matching (5% of expected width, min 3.0px)
- Contextual boosting: OCR-based anchor word detection (+2.0 confidence for "with", "and", etc.)
- Tracking offset calibration guidance in font detection output
- Safe header function with explicit dtype enforcement and memory layout safety
- **Evidence Card Visual Redesign**: Complete overhaul of evidence card generation for TV crime show style presentation
  - Panel 1: X-Ray split-view with 50% opacity overlay and green vertical guidelines
  - Panel 2: High-visibility white text (220 opacity) instead of invisible black-on-black
  - Panel 3: Letter outline wireframe overlay using Canny edge detection, replacing abstract bar charts
  - Magnifying glass annotation for artifact highlighting with detailed position information

### Fixed
- Letter reconstruction script dimension mismatch (color/grayscale space)
- Safe header function now properly handles both BGR and grayscale images
- "Kellen" match now passes with dynamic tolerance (5px error within 13.35px tolerance)
- Evidence card generation panel height calculation (fixed dimension mismatch error)

### Changed
- Tolerance changed from fixed 3.0px to dynamic 5% (minimum 3.0px)
- Forensic reports now show tolerance used and context boost information
- Evidence cards use cv2.FONT_HERSHEY_DUPLEX for bolder, more readable headers
- All evidence card panels now use high-contrast colors (green guidelines, cyan outlines, red markers)

## [0.2.0] - 2026-02-05 10:15:00 UTC

### Added

#### Automated Font Detection (Major Feature)
- **FontProfiler class**: Complete typographic profiling module (`font_profiler.py`)
  - OCR-based reference word scanning from unredacted document text
  - Multi-font testing across 9 font families (serif and sans-serif)
  - Size variation testing (10-14pt in 0.1-0.5pt increments)
  - Tracking offset detection (-0.5px to +1.0px range)
  - Kerning mode detection (metric vs standard)
  - Sub-1% width accuracy calibration
  - Profile save/load functionality (JSON format)

#### Command Line Interface
- `--file`: Specify custom PDF file path
- `--font`: Override font path (fallback if profiling disabled)
- `--csv`: Specify custom candidates CSV file
- `--dpi`: Set document DPI (default: 1200)
- `--no-profile`: Skip automatic font profiling
- `--save-profile`: Save detected profile to JSON file

#### Integration
- Modified `unredactron.py` to integrate FontProfiler
- Three-step analysis workflow:
  1. Automatic Font Detection
  2. Candidate Loading
  3. Redaction Analysis
- Forensic profile display in results output
- Calibrated width calculations using scale factor and tracking offset

#### Documentation
- Updated README.md with automated font detection features
- Updated QUICKSTART.md with new usage patterns and examples
- Added CHANGELOG.md with ISO 8601 timestamp format

### Changed
- Width calculations now use detected scale factor instead of basic DPI scaling
- Width calculations include tracking offset adjustments
- Font size now detected automatically instead of hardcoded 12pt
- Main script requires argparse (previously used hardcoded paths)

### Technical Details
- Font search space: 9 fonts × 7 sizes × 9 tracking values = 567 configurations
- Reference word detection confidence threshold: 80%
- Minimum profile accuracy for acceptance: 90%
- Calibration validation levels:
  - 99%+ : EXCELLENT - Ready for forensic analysis
  - 95%+ : GOOD - Acceptable for analysis
  - <95% : MODERATE - Results may have reduced accuracy

### Dependencies (No new dependencies required)
- Uses existing: pytesseract, PIL, pdf2image, opencv-python, numpy

## [0.1.0] - Previous Release

### Added
- Initial PDF redaction forensic analyzer
- Width-based redaction analysis
- Candidate database support (CSV format)
- Basic OpenCV redaction detection
- Confidence scoring system
- 40+ helper scripts for forensic analysis
- Forensic halo artifact detection
- Diagnostic sheet generation

---

## Changelog Format

Entries follow this format:
```
## [Version] - YYYY-MM-DD HH:MM:SS TZ

### Added / Changed / Deprecated / Removed / Fixed
- **Feature Name**: Description
  - Technical detail 1
  - Technical detail 2
- Bullet point for smaller changes
```

Timestamps use ISO 8601 format with timezone indication.
