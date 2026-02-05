.PHONY: help setup install test analyze forensic clean demo

# Default target
help:
	@echo "Unredactron - PDF Redaction Forensic Analyzer"
	@echo ""
	@echo "Quick Start:"
	@echo "  make setup     - Install all dependencies"
	@echo "  make demo      - Run demo on sample PDF"
	@echo "  make analyze   - Run basic analysis"
	@echo ""
	@echo "Analysis Commands:"
	@echo "  make forensic  - Run full forensic analysis with diagnostic sheets"
	@echo "  make halo      - Run halo extraction only"
	@echo "  make test      - Verify installation"
	@echo ""
	@echo "Documentation:"
	@echo "  cat QUICKSTART.md    - 5-minute getting started guide"
	@echo "  cat README.md        - Full documentation"
	@echo ""

# Install all dependencies
setup:
	@echo "Installing dependencies..."
	@bash scripts/setup.sh

# Install dependencies only (quick)
install:
	@echo "Installing Python packages with uv..."
	@uv pip install opencv-python-headless pdf2image pytesseract pandas Pillow numpy
	@echo "✓ Python packages installed"
	@echo ""
	@echo "System dependencies (install manually if needed):"
	@echo "  sudo apt-get install poppler-utils tesseract-ocr  # Ubuntu/Debian"
	@echo "  brew install poppler tesseract                      # macOS"

# Verify installation
test:
	@echo "Verifying installation..."
	@echo ""
	@echo "Python packages:"
	@python3 -c "import cv2; print('  ✓ opencv-python')" || echo "  ✗ opencv-python missing"
	@python3 -c "import pdf2image; print('  ✓ pdf2image')" || echo "  ✗ pdf2image missing"
	@python3 -c "import pytesseract; print('  ✓ pytesseract')" || echo "  ✗ pytesseract missing"
	@python3 -c "import pandas; print('  ✓ pandas')" || echo "  ✗ pandas missing"
	@python3 -c "import PIL; print('  ✓ Pillow')" || echo "  ✗ Pillow missing"
	@echo ""
	@echo "System commands:"
	@command -v pdftoppm >/dev/null && echo "  ✓ pdftoppm (poppler)" || echo "  ✗ pdftoppm missing"
	@command -v tesseract >/dev/null && echo "  ✓ tesseract" || echo "  ✗ tesseract missing"

# Run basic analysis
analyze:
	@echo "Running basic analysis..."
	@uv run python unredactron.py

# Run forensic analysis with diagnostic sheets
forensic:
	@echo "Running full forensic analysis..."
	@uv run python helpers/unredactron_forensic.py \
		--file files/EFTA00037366.pdf \
		--font fonts/fonts/times.ttf \
		--csv candidates.csv \
		--diagnostic-mode
	@echo ""
	@echo "Results:"
	@echo "  Report: forensic_report.txt"
	@echo "  Sheets: forensic_output/"

# Run halo extraction only
halo:
	@echo "Running halo extraction..."
	@uv run python helpers/forensic_halo.py

# Demo - quick test run
demo:
	@echo "Running demo on sample PDF..."
	@echo ""
	@uv run python unredactron.py | head -40

# Clean output files
clean:
	@echo "Cleaning output files..."
	@rm -rf forensic_output/
	@rm -rf artifacts/
	@rm -rf protrusion_analysis/
	@rm -f forensic_report.txt
	@echo "✓ Cleaned"

# Analyze custom PDF
analyze-custom:
	@echo "Analyzing custom PDF..."
	@if [ -z "$(PDF)" ]; then \
		echo "Usage: make analyze-custom PDF=path/to/file.pdf"; \
		exit 1; \
	fi
	@uv run python unredactron.py "$(PDF)"
