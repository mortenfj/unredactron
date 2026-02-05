# analyze_artifacts.py

## Purpose

**Visual artifact analysis** of images already saved by **detect_artifacts.py**. Loads PNGs from the artifact output directory, locates the red rectangle (redaction box) in each image, and reports statistics on the “halo” region (pixels outside the box): brightness range, mean, std, and distribution over dark/mid/light ranges. Optionally notes potential letter traces and edge artifacts.

## Location

- **Path:** `helpers/analyze_artifacts.py`

## Dependencies

- `cv2`, `numpy`, `os` (no PDF or Tesseract; works on PNGs only)

## Configuration

| Variable | Meaning | Default |
|----------|---------|---------|
| `ARTIFACT_DIR` | Directory containing artifact PNGs from detect_artifacts | `"artifacts"` |

## Algorithm

1. **List artifact files**  
   All `.png` files in `ARTIFACT_DIR`, sorted. Prints count.

2. **Sample analysis**  
   Takes the first 3 artifact files. For each:
   - Load image with `cv2.imread`, convert to grayscale.
   - **Red box detection:** `cv2.inRange` for red (e.g. BGR [0,0,200]–[50,50,255]). Find min/max row and column of red pixels to get box bounds and size.
   - **Halo region:** Expand box by 5 px; mask out the box so halo = pixels outside the red box but inside the expanded region. (Note: code uses a simplified halo mask; intent is to analyze pixels adjacent to the box.)
   - **Halo stats:** Among halo pixels: total count, min/max/mean/std brightness.
   - **Pixel distribution:** Count pixels in bands: very dark (<50), dark (50–100), mid (100–200), light (≥200). Print counts and percentages.
   - **Letter-like patterns:** If dark+very_dark > 0, print “Potential letter traces” and optionally edge artifact counts (implementation may vary).
   - Print path to the artifact image for manual inspection.

3. **Summary**  
   Reminder that all artifact images are in `ARTIFACT_DIR`, with short instructions for manual inspection (look for dark pixels near the red box, enhanced contrast).

## Output

- “VISUAL ARTIFACT ANALYSIS” header.
- Number of artifact images found.
- For each of the first 3 samples: filename, image size, redaction box size, “Halo Analysis” (pixel count, brightness range, mean, std), “Pixel Distribution” table, optional “Artifact Detection” line, and path to the file.
- “SUMMARY” with path to `ARTIFACT_DIR` and manual inspection tips.

## Execution

```bash
python helpers/analyze_artifacts.py
```

Run **detect_artifacts.py** first to populate `ARTIFACT_DIR`. Edit `ARTIFACT_DIR` if you use a different folder.

## Use Case

- Quantitative follow-up on artifact images produced by **detect_artifacts.py**.
- Compare halo brightness and distribution across samples.
- Guide manual inspection (which images to open, what to look for).

## See Also

- **detect_artifacts.md** — Generates the artifact images and halo metrics at 600 DPI.
- **pattern_match.md** — Compares rendered text edges to artifact edges in the full PDF.
