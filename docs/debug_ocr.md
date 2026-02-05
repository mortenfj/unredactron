# debug_ocr.py

## Purpose

**Debug script** to inspect what Tesseract OCR detects on the first page of a PDF. Prints every detected text element with confidence and bounding box (position and size), a summary of all detected words (first 100), and a list of potential control words (short, capitalized words suitable for calibration).

## Location

- **Path:** `helpers/debug_ocr.py`

## Dependencies

- `pytesseract`, `numpy`, `pdf2image`, `cv2`

## Configuration

| Variable | Meaning | Default |
|----------|---------|---------|
| `FILE_PATH` | Target PDF | `"files/EFTA00037366.pdf"` |

## Algorithm

1. **Load PDF**  
   `convert_from_path(FILE_PATH)`, first page to BGR. Print page count and “Loading …”.

2. **Run OCR**  
   `pytesseract.image_to_data(img_bgr, output_type=pytesseract.Output.DICT)`. Print image size and “Running OCR …”.

3. **Print detected text**  
   For each index in `data['text']`: text (stripped), confidence (int; -1 → 0). If text non-empty and confidence > 30: print `[conf%] 'text' at (x,y) size: w×h px` and append text to `found_words`.

4. **Summary of words**  
   Print “SUMMARY OF ALL DETECTED WORDS” and the first 100 words joined by space.

5. **Potential control words**  
   From `found_words`, keep words with length 4–10 and first character uppercase. Print “POTENTIAL CONTROL WORDS” and sorted list.

## Output

- “Loading …”, “Loaded N pages”, page 1 size.
- “Running OCR to find all text”, “Found M text elements”.
- “DETECTED TEXT (with confidence and position)”: one line per confident detection.
- “SUMMARY OF ALL DETECTED WORDS”: first 100 words.
- “POTENTIAL CONTROL WORDS”: list of short capitalized words.

## Execution

```bash
python helpers/debug_ocr.py
```

Edit `FILE_PATH` as needed. No CLI arguments.

## Use Case

- Verify that the control word you plan to use (e.g. “Subject”, “Contacts”) is detected and at what confidence/position.
- Find alternative control words if the default is missing or low confidence.
- Debug calibration failures (e.g. control word not found) by checking what OCR actually sees.

## See Also

- **main.md** / **unredactron.md** — Use `CONTROL_WORD` in calibration.
- **detect_font.md** — Picks control word from OCR automatically.
- **CLAUDE.md** — OCR calibration notes.
