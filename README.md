# Unredactron

**PDF Redaction Forensic Analyzer** - Identify redacted text through automated typographic profiling and width analysis.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-Educational%20Use%20Only-yellow.svg)](LICENSE)

## 🆕 Automated Font Detection (Latest)

Unredactron now features **automatic font detection** - no more manual font selection! The system:

- ✅ **Scans documents** for unredacted reference words using OCR
- ✅ **Tests 9+ fonts** across multiple sizes and tracking values
- ✅ **Detects kerning and spacing** adjustments automatically
- ✅ **Achieves sub-1% accuracy** with forensic-grade calibration
- ✅ **Saves profiles** for consistent analysis across multiple documents

## 🚀 Quick Start (5 minutes)

```bash
# One-line setup
make setup

# Run your first analysis
make demo
```

**Don't want to use Make?** See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

## ✨ What It Does

Unredactron analyzes poorly-redacted PDF documents to identify the hidden text beneath black redaction bars:

- **Automated Font Detection**: Scans document to detect font family, size, tracking, and kerning
- **Width Analysis**: Measures redaction boxes and compares against candidate names with sub-1% accuracy
- **Artifact Detection**: Finds anti-aliasing traces at redaction edges
- **Forensic Validation**: Generates diagnostic sheets and evidence cards for manual verification
- **Visual Evidence Cards**: TV crime show style composite images with three-panel analysis
- **Proven Results**: Successfully identified "Marcinkova", "Kellen", and "Clinton" in real documents

### Example Output

```
====================================================================================================
FORENSIC DOCUMENT PROFILE
====================================================================================================
  Detected Font:     cour.ttf
  Font Size:         10.0 pt
  Tracking Offset:   +0.00 px
  Kerning Mode:      metric
  Scale Factor:      14.2857
  Confidence:        100.0%
  Reference:         'Contact' (600.0px)
  Accuracy Score:    100.00%
====================================================================================================

Rank   Name              Position      Size         Width       Diff      Error     Conf
------------------------------------------------------------------------------------------------
1      Haskell           (3625, 5037)  600x213      600.0px     0.0px     0.0%     +     ★★★
2      Sarah             (2725, 6613)  437x212      428.6px     8.4px     2.0%     ++    ★★
3      Robert Kuhn       (2475, 3462)  962x213      942.9px    19.1px     2.0%     ++    ★★
```

## 📋 Common Commands

### Basic Usage (Automatic Font Detection)

```bash
# Run with automatic font detection (default)
python unredactron.py

# Analyze custom PDF with auto-detected font
python unredactron.py --file files/my_document.pdf

# Save detected profile for reuse
python unredactron.py --save-profile profile.json
```

### Advanced Usage

```bash
# Analyze your own PDF (with manual font override)
python unredactron.py \
    --file files/my_document.pdf \
    --font fonts/fonts/times.ttf \
    --csv candidates.csv

# Skip automatic profiling, use specified font only
python unredactron.py --no-profile --font fonts/fonts/arial.ttf

# Full forensic analysis with diagnostic sheets
uv run python helpers/unredactron_forensic.py \
    --file files/my_document.pdf \
    --font fonts/fonts/times.ttf \
    --csv candidates.csv \
    --diagnostic-mode

# Artifact detection only
uv run python helpers/forensic_halo.py

# Generate visual evidence cards (TV crime show style)
uv run python helpers/generate_evidence_card.py \
    --pdf files/my_document.pdf \
    --redaction-index 0 \
    --candidate-name "Kellen" \
    --highlight-pos 2

# Evidence card options:
#   --highlight-pos N    : Highlight specific character position (0-indexed)
#   --output-dir DIR     : Custom output directory (default: evidence_cards/)
#   --dpi N             : Document DPI (default: 600)
```

### Evidence Cards

The evidence card generator creates composite images showing three types of forensic evidence:

1. **Panel 1 - Geometric Fit (X-Ray View)**
   - Top: Original redaction
   - Middle: 50% opacity overlay showing candidate name "inside" the box
   - Bottom: Candidate name rendered in black
   - Green vertical guidelines prove perfect width alignment

2. **Panel 2 - Contextual Fit (Fill-in-the-Blank)**
   - Shows candidate name "restored" to the document
   - High-visibility white text (220 opacity) clearly visible against black redaction
   - Red box outlines the redaction area for reference

3. **Panel 3 - Artifact Fingerprint (Letter Outline)**
   - Cyan wireframe letter outlines overlaid on enhanced artifact pixels
   - Allows visual alignment of letter shapes (ascenders, descenders) with noise
   - Optional magnifying glass annotation for specific character positions
   - Shows artifact detection percentage for each character position

## 📁 Project Structure

```
unredactron/
├── unredactron.py              # Main analyzer with auto font detection ⭐ NEW
├── font_profiler.py            # Typographic profiling module ⭐ NEW
├── helpers/
│   ├── generate_evidence_card.py  # Visual evidence card generator ⭐ NEW
│   ├── forensic_halo.py        # Advanced artifact detection
│   ├── unredactron_forensic.py # Integrated analyzer
│   ├── detect_font.py          # Standalone font detection
│   └── ...                     # 40+ analysis scripts
├── files/                      # Put your PDFs here
├── fonts/                      # Font library (9 fonts)
├── candidates.csv              # Suspect database (920 entries)
├── evidence_cards/             # Generated evidence card images
├── CHANGELOG.md                # Version history with timestamps ⭐ NEW
├── Makefile                    # Convenient commands
└── scripts/
    └── setup.sh                # One-line setup script
```

## 🎯 Key Features

### Automated Font Profiling ⭐ NEW

1. **OCR Reference Scanning** - Finds unredacted text automatically
2. **Font Library Search** - Tests 9+ fonts across 7 sizes with 9 tracking values
3. **Tracking/Kerning Detection** - Calculates letter-spacing offsets automatically
4. **Sub-1% Accuracy** - Forensic-grade calibration with confidence scoring
5. **Profile Reuse** - Save and load profiles for batch processing

### Three-Pillar Analysis

1. **Width Matching** - Compare redaction width to expected text width
2. **Artifact Detection** - Find anti-aliasing traces at edges
3. **Confidence Scoring** - Use contextual intelligence from database

### Advanced Forensic Halo Extraction

The `forensic_halo.py` module implements state-of-the-art artifact detection:

- **Corner Exclusion** - Removes noise from sharp corners
- **Side-Wall Separation** - Isolates top/bottom/left/right edges
- **Forensic Enhancement** - Contrast stretching, bit-plane slicing, ELA
- **Diagnostic Sheets** - Composite visualizations for manual verification

See [docs/FORENSIC_HALO.md](docs/FORENSIC_HALO.md) for details.

### Intelligent Candidate Database

- **920 suspects** including name variants and alternative spellings
- **Confidence scoring** - Boost confirmed matches
- **Self-documenting** - CSV includes notes and sources

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](QUICKSTART.md) | **Start here** - 5-minute setup guide |
| [README.md](README.md) | This file - overview and common commands |
| [CHANGELOG.md](CHANGELOG.md) | Version history with timestamps |
| [README_UNREDACTRON.md](README_UNREDACTRON.md) | Detailed user guide |
| [docs/FORENSIC_HALO.md](docs/FORENSIC_HALO.md) | Advanced artifact detection |
| [helpers/README.md](helpers/README.md) | Development scripts index |
| [docs/](docs/) | Complete documentation index |

## 🔧 Installation

### Option 1: Automated (Recommended)

```bash
make setup
```

### Option 2: Manual

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python dependencies
uv pip install opencv-python-headless pdf2image pytesseract pandas Pillow

# Install system dependencies
sudo apt-get install poppler-utils tesseract-ocr  # Ubuntu/Debian
brew install poppler tesseract                      # macOS
```

## 🧪 How It Works

1. **Convert PDF** → High-resolution image (1200 DPI)
2. **Automatic Font Profiling** → Scan for reference word, detect font/size/tracking
3. **Detect Redactions** → Find black boxes using OpenCV
4. **Calculate Widths** → Render each candidate with calibrated font settings
5. **Compare & Rank** → Match actual vs expected widths (sub-1% accuracy)
6. **Verify Artifacts** → Check for anti-aliasing traces (optional)
7. **Generate Report** → Output matches with confidence scores and profile details

## 🎓 Use Cases

- **Legal Research** - Identify redacted names in court documents
- **Journalism** - Verify redacted claims in public records
- **Security Research** - Study redaction failure patterns
- **Document Review** - Check if redactions were properly applied

## ⚠️ Important Notes

- **Font Matching Critical** - Must match document's original font
- **High DPI Required** - Works best on 600+ DPI scans
- **Clean Redactions** - Professional redactions may leave no traces
- **Educational Use** - For authorized document analysis only

## 🔬 Proven Results

Successfully identified redacted text in real documents:

✅ **"Marcinkova"** in "Attempts were made to [NAME] and Brunel" (0.4% error)
✅ **"Kellen"** in multiple redactions (1.5% error)
✅ **"Clinton"** in multiple redactions (0.0% error)

## 🤝 Contributing

This is a security research tool. Contributions welcome:
- New font detection algorithms
- Improved artifact detection
- Additional reconstruction techniques
- Documentation improvements

## 📄 License

Educational and research use only. See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Built for forensic document analysis and security research. Uses OpenCV, Tesseract OCR, and PIL for image processing.

---

**Ready to start?** Run `make setup` then `make demo`
