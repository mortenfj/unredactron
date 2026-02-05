#!/usr/bin/env bash
# Unredactron Setup Script
# This script installs all dependencies and verifies the setup

set -e  # Exit on error

echo "===================================================================================================="
echo "UNREDACTRON - Setup Script"
echo "===================================================================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_step() { echo ""; echo "[$(date +'%H:%M:%S')] $1"; }

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if command -v apt-get &> /dev/null; then
            PKG_MANAGER="apt-get"
        elif command -v yum &> /dev/null; then
            PKG_MANAGER="yum"
        else
            print_error "Unsupported Linux package manager"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PKG_MANAGER="brew"
    else
        print_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
    print_success "Detected OS: $OS with $PKG_MANAGER"
}

# Check uv installation
check_uv() {
    print_step "Checking uv installation..."

    if command -v uv &> /dev/null; then
        UV_VERSION=$(uv --version)
        print_success "uv installed: $UV_VERSION"
    else
        print_error "uv not found"
        echo ""
        echo "Install uv with:"
        echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo ""
        exit 1
    fi
}

# Install system dependencies
install_system_deps() {
    print_step "Installing system dependencies..."

    if [[ "$OS" == "linux" ]]; then
        if [[ "$PKG_MANAGER" == "apt-get" ]]; then
            echo "Checking for poppler-utils and tesseract-ocr..."

            if ! dpkg -l | grep -q poppler-utils; then
                echo "Installing poppler-utils..."
                sudo apt-get update -qq
                sudo apt-get install -y poppler-utils
            else
                print_success "poppler-utils already installed"
            fi

            if ! dpkg -l | grep -q tesseract-ocr; then
                echo "Installing tesseract-ocr..."
                sudo apt-get install -y tesseract-ocr
            else
                print_success "tesseract-ocr already installed"
            fi
        elif [[ "$PKG_MANAGER" == "yum" ]]; then
            sudo yum install -y poppler-utils tesseract
        fi
    elif [[ "$OS" == "macos" ]]; then
        if ! brew list poppler &> /dev/null; then
            echo "Installing poppler..."
            brew install poppler
        else
            print_success "poppler already installed"
        fi

        if ! brew list tesseract &> /dev/null; then
            echo "Installing tesseract..."
            brew install tesseract
        else
            print_success "tesseract already installed"
        fi
    fi
}

# Install Python dependencies with uv
install_python_deps() {
    print_step "Installing Python dependencies..."

    # Required packages
    PACKAGES=(
        "opencv-python-headless"
        "pdf2image"
        "pytesseract"
        "pandas"
        "Pillow"
        "numpy"
    )

    for package in "${PACKAGES[@]}"; do
        echo "  → Installing $package..."
        uv pip install "$package" > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            print_success "$package installed"
        else
            print_error "Failed to install $package"
        fi
    done
}

# Verify installation
verify_installation() {
    print_step "Verifying installation..."

    # Check Python packages
    python3 -c "import cv2" 2>/dev/null && print_success "opencv-python" || print_error "opencv-python missing"
    python3 -c "import pdf2image" 2>/dev/null && print_success "pdf2image" || print_error "pdf2image missing"
    python3 -c "import pytesseract" 2>/dev/null && print_success "pytesseract" || print_error "pytesseract missing"
    python3 -c "import pandas" 2>/dev/null && print_success "pandas" || print_error "pandas missing"
    python3 -c "import PIL" 2>/dev/null && print_success "Pillow" || print_error "Pillow missing"
    python3 -c "import numpy" 2>/dev/null && print_success "numpy" || print_error "numpy missing"

    # Check system commands
    command -v pdftoppm &> /dev/null && print_success "pdftoppm (poppler)" || print_error "pdftoppm missing"
    command -v tesseract &> /dev/null && print_success "tesseract OCR" || print_error "tesseract missing"
}

# Test run on sample PDF
test_run() {
    print_step "Testing with sample PDF..."

    if [ -f "files/EFTA00037366.pdf" ]; then
        echo "Running quick analysis..."
        uv run python unredactron.py > /tmp/unredactron_test.log 2>&1

        if [ $? -eq 0 ]; then
            print_success "Analysis completed successfully"
            echo ""
            echo "Sample output:"
            head -20 /tmp/unredactron_test.log | tail -10
        else
            print_warning "Test run had issues. Check /tmp/unredactron_test.log"
        fi
    else
        print_warning "Sample PDF not found (files/EFTA00037366.pdf)"
    fi
}

# Print next steps
print_next_steps() {
    echo ""
    echo "===================================================================================================="
    echo "Setup Complete!"
    echo "===================================================================================================="
    echo ""
    echo "Quick Start:"
    echo "  uv run python unredactron.py                                    # Run basic analysis"
    echo "  uv run python helpers/forensic_halo.py                         # Advanced artifact detection"
    echo "  uv run python helpers/unredactron_forensic.py --diagnostic-mode # Full forensic analysis"
    echo ""
    echo "Documentation:"
    echo "  cat QUICKSTART.md    # 5-minute getting started guide"
    echo "  cat README.md        # Full documentation"
    echo "  cat docs/FORENSIC_HALO.md  # Advanced forensic techniques"
    echo ""
}

# Main setup flow
main() {
    detect_os
    check_uv
    install_system_deps
    install_python_deps
    verify_installation
    test_run
    print_next_steps
}

# Run main function
main
