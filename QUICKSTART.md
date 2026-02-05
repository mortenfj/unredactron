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
# Analyze the included sample PDF
uv run python unredactron.py
```

**Expected output:**
```
====================================================================================================
UNREDACTRON - PDF Redaction Forensic Analyzer
====================================================================================================

[INFO] Loading document: files/EFTA00037366.pdf
[INFO] Converting to 1200 DPI image...
[INFO] Found 16 redaction boxes
[INFO] Loaded 920 candidates from candidates.csv

Rank   Name              Position      Size         Width       Diff      Error     Conf
------------------------------------------------------------------------------------------------
1      Clinton           (3625, 5037)  600x213      600.1px     0.1px     0.0%     +++++ ★★★
...
```

## What Just Happened?

1. **PDF → Image**: Converted PDF to high-resolution image (1200 DPI)
2. **Found Redactions**: Detected 16 black redaction boxes
3. **Width Matching**: Compared each redaction's width against 920 candidate names
4. **Ranked Results**: Displayed matches sorted by accuracy

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

# 3. Run analysis
uv run python unredactron.py
```

## Common Commands

```bash
# Basic analysis
uv run python unredactron.py

# With custom PDF
uv run python helpers/unredactron_forensic.py --file files/my.pdf --font fonts/fonts/times.ttf

# Just artifact detection (no width matching)
uv run python helpers/forensic_halo.py

# Font detection
uv run python helpers/detect_font.py
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
- Check that the font matches your document (edit `--font` parameter)
- Try increasing tolerance with `--tolerance 5.0`
- Verify names in `candidates.csv` match the document's font and style

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [docs/FORENSIC_HALO.md](docs/FORENSIC_HALO.md) for advanced artifact detection
- See [helpers/README.md](helpers/README.md) for development tools

## Need Help?

1. Check the [documentation index](docs/README.md)
2. Review [sample outputs](files/) in the repository
3. Examine [forensic sheets](forensic_output/) after running `--diagnostic-mode`
