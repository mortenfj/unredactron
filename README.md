# Unredactron

**PDF Redaction Forensic Analyzer** - Identify redacted text through width analysis and artifact detection.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-Educational%20Use%20Only-yellow.svg)](LICENSE)

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

- **Width Analysis**: Measures redaction boxes and compares against candidate names
- **Artifact Detection**: Finds anti-aliasing traces at redaction edges
- **Forensic Validation**: Generates diagnostic sheets for manual verification
- **Proven Results**: Successfully identified "Marcinkova", "Kellen", and "Clinton" in real documents

### Example Output

```
Rank   Name              Position      Size         Width       Diff      Error     Conf
------------------------------------------------------------------------------------------------
1      Marcinkova        (281, 2519)   369x106      369.2px     0.2px     0.4%     +++++ ★★★
2      Kellen            (900, 337)    2263x106     2265.1px    2.1px     0.9%     ++++  ★★★
3      Clinton           (3625, 5037)  600x213      600.1px     0.1px     0.0%     +++++ ★★★
```

## 📋 Common Commands

### Basic Usage

```bash
make analyze              # Run basic width-matching analysis
make forensic             # Full forensic analysis with diagnostic sheets
make halo                 # Artifact detection only
```

### Advanced Usage

```bash
# Analyze your own PDF
uv run python helpers/unredactron_forensic.py \
    --file files/my_document.pdf \
    --font fonts/fonts/times.ttf \
    --csv candidates.csv \
    --diagnostic-mode

# Font detection
uv run python helpers/detect_font.py

# Custom PDF with Make
make analyze-custom PDF=path/to/file.pdf
```

## 📁 Project Structure

```
unredactron/
├── unredactron.py              # Main analyzer (CSV-based)
├── helpers/
│   ├── forensic_halo.py        # Advanced artifact detection ⭐ NEW
│   ├── unredactron_forensic.py # Integrated analyzer ⭐ NEW
│   ├── detect_font.py          # Automated font detection
│   └── ...                     # 40+ analysis scripts
├── files/                      # Put your PDFs here
├── fonts/                      # Font library
├── candidates.csv              # Suspect database (920 entries)
├── Makefile                    # Convenient commands
└── scripts/
    └── setup.sh                # One-line setup script
```

## 🎯 Key Features

### Three-Pillar Analysis

1. **Width Matching** - Compare redaction width to expected text width
2. **Artifact Detection** - Find anti-aliasing traces at edges
3. **Confidence Scoring** - Use contextual intelligence from database

### Advanced Forensic Halo Extraction ⭐

The new `forensic_halo.py` module implements state-of-the-art artifact detection:

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
2. **Detect Redactions** → Find black boxes using OpenCV
3. **Calculate Widths** → Render each candidate in matching font
4. **Compare & Rank** → Match actual vs expected widths
5. **Verify Artifacts** → Check for anti-aliasing traces (optional)
6. **Generate Report** → Output matches with confidence scores

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
