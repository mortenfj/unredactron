# Forensic Halo Extraction Module

## Overview

The Forensic Halo Extraction module is an advanced artifact detection system for analyzing redacted PDF documents. It implements sophisticated computer vision techniques to detect and analyze residual pixel traces around redaction boundaries - where font anti-aliasing or compression artifacts may persist.

## Features

### 1. Halo Extraction with Corner Exclusion

The module extracts a "halo" region around each redaction box - the pixels immediately adjacent to the redaction boundaries. Crucially, it implements **corner exclusion** to remove noise from sharp corners where compression artifacts are most severe.

**Key parameters:**
- `halo_thickness`: Width of edge buffer zone (default: 6 pixels)
- `corner_radius`: Radius of corner exclusion zone (default: 15 pixels)

### 2. Side-Wall Separation

The halo is split into four distinct slivers:
- **Top Wall**: Critical for identifying ascenders (l, t, h, f, k, b, d)
- **Bottom Wall**: Critical for identifying descenders (g, j, p, q, y)
- **Left Wall**: Detects letter protrusions on the left edge
- **Right Wall**: Detects letter protrusions on the right edge

### 3. Forensic Enhancement Pipeline

Multiple image processing techniques to make artifacts visible:

| Technique | Purpose |
|-----------|---------|
| **Extreme Contrast Stretching** | Amplifies near-white pixels from font anti-aliasing |
| **Canny Edge Detection** | Traces structural outlines of letter shapes |
| **Bit-Plane Slicing** | Examines least significant bits where subtle modifications may exist |
| **Error Level Analysis (ELA)** | Identifies compression level differences indicating multi-layer modifications |

### 4. Diagnostic Mode

When enabled, generates composite "forensic sheets" for each redaction showing:
- Original redaction box
- Full halo with corners excluded
- All four side-wall extractions
- All enhancement views
- Optional candidate name overlay

## Installation

```bash
# Install dependencies with uv
uv pip install opencv-python-headless pdf2image Pillow pandas

# System dependencies for PDF processing
sudo apt-get install poppler-utils
```

## Usage

### Basic Standalone Analysis

```bash
# Run forensic halo analysis on a PDF
uv run python helpers/forensic_halo.py

# Analyze a specific file
uv run python helpers/forensic_halo.py files/document.pdf
```

### Integrated Analysis (Width Matching + Artifacts)

```bash
# Basic usage with candidate names
uv run python helpers/unredactron_forensic.py \
    --file files/document.pdf \
    --font fonts/fonts/times.ttf \
    --candidates "Sarah Kellen" "Ghislaine Maxwell" "Jeffrey Epstein"

# Using CSV with confidence scores
uv run python helpers/unredactron_forensic.py \
    --file files/document.pdf \
    --font fonts/fonts/times.ttf \
    --csv candidates.csv \
    --diagnostic-mode

# With calibration word for accuracy
uv run python helpers/unredactron_forensic.py \
    --file files/document.pdf \
    --font fonts/fonts/times.ttf \
    --csv candidates.csv \
    --control-word "Subject" \
    --diagnostic-mode
```

### Command-Line Options

```
--file              Path to PDF document (required)
--font              Path to TrueType font file (required)
--csv               Path to CSV with candidates (columns: name, confidence)
--candidates        Candidate names (space-separated)
--dpi               DPI for PDF conversion (default: 600)
--tolerance         Width tolerance in pixels (default: 3.0)
--control-word      Visible word for calibration
--diagnostic-mode   Generate forensic sheets
--output            Report output path (default: forensic_report.txt)
```

## Python API

### Using the ForensicHaloExtractor Class

```python
from helpers.forensic_halo import ForensicHaloExtractor
from pdf2image import convert_from_path
import cv2
import numpy as np

# Convert PDF to image
images = convert_from_path("document.pdf", dpi=600)
img = np.array(images[0])
gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

# Initialize extractor
extractor = ForensicHaloExtractor(
    dpi=600,
    halo_thickness=6,
    corner_radius=15
)

# Extract halo with corner exclusion
redaction = (x, y, w, h)  # Redaction bounding box
halo_data = extractor.extract_halo_with_corner_exclusion(gray, redaction)

# Apply forensic enhancements
enhanced = extractor.apply_forensic_enhancement(halo_data['full'])

# Analyze for artifacts
metrics = extractor.analyze_halo_for_artifacts(halo_data)

# Generate forensic sheet
extractor.create_forensic_sheet(
    gray,
    halo_data,
    enhanced,
    redaction,
    candidate_name="Suspect Name",
    output_path="forensic_sheet.png"
)
```

### Using the Integrated Analyzer

```python
from helpers.unredactron_forensic import ForensicRedactionAnalyzer

# Initialize analyzer
analyzer = ForensicRedactionAnalyzer(
    file_path="files/document.pdf",
    font_path="fonts/fonts/times.ttf",
    dpi=600,
    diagnostic_mode=True,
    tolerance=3.0
)

# Calibrate with visible word
scale_factor = analyzer.calibrate_with_control_word("Subject")

# Find redactions
redactions = analyzer.find_redactions()

# Match candidates
candidates = [
    {"name": "Sarah Kellen", "confidence": 0.9},
    {"name": "Ghislaine Maxwell", "confidence": 0.95}
]
matches = analyzer.match_candidates_to_redactions(
    candidates=candidates,
    redactions=redactions,
    scale_factor=scale_factor
)

# Generate report
analyzer.generate_report(matches, "report.txt")
```

## Output

### Forensic Sheets

Each forensic sheet is a composite image showing:

```
+------------------+------------------+------------------+
|  ORIGINAL        |  HALO (CORNERS   |  CONTRAST        |
|  REDACTION       |  EXCLUDED)       |  STRETCHED       |
+------------------+------------------+------------------+
|  TOP WALL        |  BOTTOM WALL     |  LEFT WALL       |
|                  |                  |  RIGHT WALL      |
+------------------+------------------+------------------+
|  CANNY EDGES     |  BIT-PLANE (LSB) |  ELA             |
+------------------+------------------+------------------+
```

### Analysis Report

Text report includes:
- Document metadata
- All matches with width scores
- Artifact confidence percentages
- Dark pixel counts per side wall
- Edge detection results

## Interpretation

### Artifact Confidence Scores

- **< 1%**: Likely clean redaction (no detectable artifacts)
- **1-5%**: Weak artifact signal (possible traces)
- **5-10%**: Moderate artifact signal (likely traces)
- **> 10%**: Strong artifact signal (clear traces)

### Side-Wall Analysis

- **High top/bottom scores**: May indicate ascenders or descenders
- **High left/right scores**: May indicate letter protrusions
- **Combined with width matching**: Confirms candidate identification

### Enhancement Views

- **Contrast Stretched**: Look for letter shapes in white regions
- **Canny Edges**: Look for structural outlines matching letters
- **Bit-Plane**: Look for patterns in LSB (potential hidden layers)
- **ELA**: Look for compression inconsistencies (potential modification)

## Technical Details

### Corner Exclusion Algorithm

Uses a diamond-shaped mask to exclude corner regions:

```
Corner exclusion mask (15px radius):
  ##\....../##
  ####\../####
  ######X######
  ####/../####
  #/......\#
```

This removes high-frequency noise from sharp corners while preserving the valuable edge regions.

### Side-Wall Extraction

Each side wall is extracted independently with corner masking applied:

```python
top = roi[y-pad:y, x:x+w]      # Above redaction
bottom = roi[y+h:y+h+pad, x:x+w]  # Below redaction
left = roi[y:y+h, x-pad:x]      # Left of redaction
right = roi[y:y+h, x+w:x+w+pad]  # Right of redaction
```

### Artifact Scoring

The artifact confidence score combines metrics from all four walls:

```
confidence = (top * 0.30) + (bottom * 0.30) + (left * 0.20) + (right * 0.20)
```

Top and bottom walls are weighted higher as they're more diagnostic for character identification.

## Limitations

1. **Font Dependency**: Requires matching the document's original font
2. **Quality Dependent**: Works best on high-DPI scans (600+ DPI)
3. **Compression Artifacts**: Heavily compressed PDFs may have fewer detectable artifacts
4. **Clean Redactions**: Professionally applied redactions may leave no traces

## Comparison with Existing Tools

| Feature | detect_artifacts.py | forensic_halo.py |
|---------|-------------------|------------------|
| Corner Exclusion | ❌ | ✅ |
| Side-Wall Separation | ❌ | ✅ |
| Contrast Stretching | ✅ Basic | ✅ Enhanced |
| Bit-Plane Slicing | ❌ | ✅ |
| Error Level Analysis | ❌ | ✅ |
| Diagnostic Sheets | ❌ | ✅ Composite |
| Width Matching | ❌ | ✅ Integrated |

## Contributing

To extend this module:

1. Add new enhancement techniques in `apply_forensic_enhancement()`
2. Improve artifact scoring in `analyze_halo_for_artifacts()`
3. Add pattern recognition for specific letter shapes
4. Integrate with OCR for automated candidate suggestions

## License

This is a security research/forensics tool. Use responsibly and only on documents you have authorization to analyze.
