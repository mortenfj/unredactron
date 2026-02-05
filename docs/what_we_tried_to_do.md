# what_we_tried_to_do.md (Methodology Notes)

## Purpose

**what_we_tried_to_do.md** is a short **methodology narrative** (not executable code). It describes the intended forensic pipeline: calibration, typographic spacing, redaction detection, brute-force width matching, and artifact verification. It explains the “why” behind the techniques used in the codebase.

## Location

- **Path:** `what_we_tried_to_do.md` (project root). Documented here in `docs/what_we_tried_to_do.md` for the docs index.

## Contents (Summary)

### Objective

- Build a **digital forensic pipeline** to identify text behind redaction bars in “True Redactions” (text layer removed), so copy-paste is not possible.

### 1. Document Calibration (Scale & Metrics)

- Document “size” depends on scan resolution (DPI). Cannot assume “12 pt = 50 px”.
- **Control word:** An unredacted word (e.g. “Subject”, “Date”) is chosen.
- **Measurement:** Script measures pixel width of that word.
- **Scale factor:** Measured width vs font’s theoretical width → scale factor so any name’s pixel width can be predicted in that document.

### 2. Typographic Spacing (Tracking)

- Documents may have non-standard spacing.
- **Tracking:** Uniform space between letters; **Kerning:** space between specific pairs.
- Script tests a range of tracking values (e.g. -0.5 to +2.0 px) per name to account for “stretching” or “squeezing” seen in examples. (Implementation may vary; see individual scripts.)

### 3. Automated Redaction Detection

- **Binarization:** Document to high-contrast black/white.
- **Contours:** OpenCV finds solid black rectangles.
- **Filtering:** Ignore small noise; keep shapes with redaction-like aspect ratio.

### 4. Brute-Force Attack

- **Width matching:** For each redaction bar, render each suspect name with calibrated font and tracking; check if width matches within a small tolerance (e.g. 0.5 px in the narrative; scripts use 3–15 px).
- **Name variations:** First Last, LAST FIRST, Last, First, etc., so formatting does not hide matches.

### 5. Artifact Verification (“Final Boss”)

- **Edge analysis:** Black box over text can leave anti-aliasing (grey pixels) at the edges — **artifacts**.
- **Pixel overlay:** Generate a “stencil” of the candidate name and overlay on the redaction; check if letter shapes align with stray pixels. (Partially implemented in detect_artifacts.py, pattern_match.py; full alignment is complex.)

### Summary of Colab Workflow

- Mount Drive; input PDF and name list; calibrate with control word; scan for black boxes; solve by identifying which names explain size and artifacts of each box.

## Use Case

- Onboarding: understand the high-level forensic strategy.
- Align new scripts or features with the intended pipeline (calibration → detection → matching → verification).
- Explain the project to others without reading every script.

## See Also

- **CLAUDE.md** — Architecture and implementation details.
- **detect_artifacts.md** / **pattern_match.md** — Artifact-related implementation.
- **main.md** / **unredactron.md** — Where calibration and width matching are implemented.
