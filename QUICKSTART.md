# Quick Start Guide

Get up and running with Unredactron in under 5 minutes.

## Prerequisites

You'll need:
- Linux or macOS (WSL2 works on Windows)
- Python 3.8+
- uv package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

## One-Line Setup

```bash
bash scripts/setup.sh
```

This installs all dependencies and verifies your setup.

## Run Your First Analysis

```bash
# Analyze the included sample PDF (automatic font detection enabled)
python unredactron.py
```

**Expected output:**
```
====================================================================================================
STEP 1: AUTOMATIC FONT DETECTION
====================================================================================================

[1] REFERENCE WORD SCAN
    ✓ Found: 'Contact' at (575, 3050)

[2] FONT SEARCH LIBRARY
    Testing 9 fonts × 7 sizes × 9 tracking values...
    ✓ Detected Font: cour.ttf, Size: 10.0pt, Confidence: 100.0%

====================================================================================================
DETECTED REDACTIONS - 16 matches found
====================================================================================================

Rank   Name              Position      Size         Width       Diff      Error     Conf
------------------------------------------------------------------------------------------------
1      Haskell           (3625, 5037)  600x213      600.0px     0.0px     0.0%     +     ★★★
...
```

## What Just Happened?

1. **PDF → Image**: Converted PDF to high-resolution image (1200 DPI)
2. **Font Profiling**: Automatically detected font, size, tracking, and kerning settings
3. **Found Redactions**: Detected 16 black redaction boxes
4. **Width Matching**: Compared each redaction's calibrated width against 920 candidates
5. **Ranked Results**: Displayed matches with sub-1% accuracy and confidence scores

## Try the Advanced Forensic Analysis

```bash
# Run with artifact detection and diagnostic sheets
uv run python helpers/unredactron_forensic.py \
    --file files/EFTA00037366.pdf \
    --font fonts/fonts/times.ttf \
    --csv candidates.csv \
    --diagnostic-mode
```

This generates:
- Text report: `forensic_report.txt`
- Forensic sheets: `forensic_output/` (visual analysis of each redaction)

## Analyze Your Own PDF

```bash
# 1. Put your PDF in the files/ directory
cp ~/Documents/my_document.pdf files/

# 2. Edit candidates.csv with your suspect names
nano candidates.csv

# 3. Run analysis (automatic font detection)
python unredactron.py --file files/my_document.pdf

# 4. Optionally save the detected profile for reuse
python unredactron.py --file files/my_document.pdf --save-profile my_profile.json
```

## Common Commands

```bash
# Basic analysis (automatic font detection)
python unredactron.py

# With custom PDF
python unredactron.py --file files/my.pdf

# Skip profiling, use specific font only
python unredactron.py --no-profile --font fonts/fonts/arial.ttf

# Advanced forensic analysis with diagnostic sheets
uv run python helpers/unredactron_forensic.py --file files/my.pdf --font fonts/fonts/times.ttf

# Just artifact detection (no width matching)
uv run python helpers/forensic_halo.py
```

## Troubleshooting

### "uv: command not found"
Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### "poppler not found"
```bash
sudo apt-get install poppler-utils tesseract-ocr  # Ubuntu/Debian
brew install poppler tesseract                      # macOS
```

### "No matches found"
- The automatic font detection may have failed - try running with `--no-profile` and specifying a font manually
- Try `python unredactron.py --no-profile --font fonts/fonts/times.ttf`
- Verify names in `candidates.csv` match the document's context

### "Font profiling failed"
- Check that the document has some unredacted text for OCR to use as reference
- Try using `--no-profile` to skip automatic detection and specify a font manually
- Ensure tesseract-ocr is installed: `sudo apt-get install tesseract-ocr`

## Need Help?

1. Check the [documentation index](docs/README.md)
2. Review [sample outputs](files/) in the repository
3. Examine [forensic sheets](forensic_output/) after running `--diagnostic-mode`
