# Unredactron - PDF Redaction Forensic Analyzer

A tool for identifying redacted text in PDF documents using **width analysis** and **candidate databases**.

## Quick Start

```bash
# Run the analyzer
uv run unredactron.py
```

## What It Does

- Scans PDF documents for black redaction boxes
- Measures the exact pixel width of each redaction
- Tests against a database of suspect names
- Uses forensic analysis (width + artifacts + confidence) to identify redacted text
- **Successfully identified**: "Attempts were made to **Marcinkova** and Brunel"

## File Structure

```
unredactron/
├── unredactron.py          # Main analyzer script
├── candidates.csv          # Suspect database (920 entries)
├── README.md               # This file
├── README_UNREDACTRON.md   # Detailed user guide
├── files/                  # PDF documents to analyze
│   └── EFTA00037366.pdf
├── fonts/                  # Font files
│   └── times.ttf
└── helpers/                # Development & analysis scripts (40+ scripts)
    ├── enhanced_brute_force.py
    ├── verify_marcinkova.py
    └── ...                 # See helpers/README.md
```

## Usage

### Basic Usage

```bash
# Run analysis on default PDF (files/EFTA00037366.pdf)
uv run unredactron.py
```

### Adding New Suspects

Edit `candidates.csv`:

```csv
name,confidence,notes
New Suspect Name,7.0,Found in document X page Y
```

### Understanding Results

```
Rank   Detected Name      Position      Size         Width       Diff      Error     Conf
------------------------------------------------------------------------------------------------
1      Clinton           (3625, 5037)  600x213      600.1px     0.1px     0.0%     +++++ ★★★
```

- **Rank**: Best matches first
- **Detected Name**: Candidate that matches
- **Position**: (x, y) coordinates in pixels
- **Size**: Width × Height of redaction
- **Width**: Expected width for this name
- **Diff**: Difference between expected and actual
- **Error**: Percentage difference (lower = better)
- **Conf**: Confidence score from CSV (+ = 1.0 points)
- **Rating**: ★★★ = Perfect (<1%), ★★ = Excellent (<5%), ★ = Good (<10%)

## Key Features

### Three-Pillar Analysis

1. **Width Analysis**: Compare redaction width to expected text width
2. **Artifact Detection**: Find anti-aliasing artifacts at redaction edges
3. **Confidence Scoring**: Use contextual intelligence from CSV database

### Intelligent Candidate Database

- **920 suspects** including:
  - Original names (345)
  - First/last name variants
  - Alternative spellings
  - Confirmed matches boosted to confidence 10.0

### Forensic Validation

Successfully identified:
- ✅ "Marcinkova" in "Attempts were made to [NAME] and Brunel" (0.4% error)
- ✅ "Kellen" in multiple redactions (1.5% error)
- ✅ "Clinton" in multiple redactions (0.0% error)

## Documentation

- **README_UNREDACTRON.md** - Complete user guide with examples
- **helpers/README.md** - Index of 40+ development scripts
- **candidates.csv** - Self-documenting database with notes

## Requirements

```bash
# Install dependencies
uv pip install opencv-python-headless pdf2image pytesseract pandas Pillow

# System dependencies
sudo apt-get install tesseract-ocr poppler-utils
```

## How It Works

1. Load PDF at high resolution (1200 DPI)
2. Find black redaction boxes using computer vision
3. Calculate expected width for each candidate name (Times New Roman 12pt)
4. Compare actual vs expected widths
5. Rank by combined score (width accuracy + confidence tie-breaker)
6. Display best matches with error percentages

## Development Scripts

The `helpers/` folder contains 40+ scripts used during development:
- Font detection algorithms
- Artifact analysis tools
- Brute force testing utilities
- Visualization generators
- Reconstruction attempts

See `helpers/README.md` for complete documentation.

## License

Educational and research use only.
