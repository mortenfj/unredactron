# Unredactron - PDF Redaction Forensic Analyzer

A tool for identifying redacted text in PDF documents using **width analysis** and **candidate databases**.

## Quick Start

```bash
# Run the analyzer
uv run unredactron.py
```

## The candidates.csv Format

Edit `candidates.csv` to add your own suspects:

```csv
name,confidence,notes
Marcinkova,5.5,Attempts were made to [NAME] and Brunel
Sarah Kellen,9.0,Confirmed match for multiple redactions
Bill Clinton,6.0,Former President
Jean-Luc Brunel,4.0,Appears unredacted in email
```

### Columns:

- **name** (required): The text to test (can be first name, last name, or full name)
- **confidence** (optional): 0-10 score indicating how likely this name is
  - Higher confidence names are preferred when width matches are similar
  - Use 9-10 for confirmed matches
  - Use 5-7 for strongly suspected names
  - Use 1-3 for common names or weak leads
  - Leave empty or 0 for untested names
- **notes** (optional): Any contextual information about this candidate

### How Confidence Scoring Works:

The system combines **width analysis** (primary) with **confidence** (secondary tie-breaker):

```
combined_score = width_error - (confidence / 10)
```

- Width match is 90% of the score
- Confidence breaks ties when widths are similar
- Example: Two names with 0.5% width error, the one with confidence 9.0 will rank higher

## Adding New Names

Simply edit `candidates.csv` and add a new line:

```csv
# Format: name,confidence,notes
New Suspect Name,7.0,Found in document X page Y
```

Then re-run `uv run unredactron.py`

## Understanding the Output

```
Rank   Detected Name      Position      Size         Width       Diff      Error     Conf
------------------------------------------------------------------------------------------------
1      Clinton           (3625, 5037)  600x213      600.1px     0.1px     0.0%     +++++ ★★★
```

- **Rank**: Order by error percentage (best first)
- **Detected Name**: The candidate that best matches
- **Position**: (x, y) coordinates in pixels
- **Size**: Width × Height of redaction
- **Width**: Expected width for this name
- **Diff**: Difference between expected and actual (smaller = better)
- **Error**: Percentage difference
- **Conf**: Confidence score from CSV (+ = 1.0 points)
- **Rating**: ★★★ = Perfect (<1%), ★★ = Excellent (<5%), ★ = Good (<10%)

## Tips for Best Results

1. **Add all name variants**: Include first name, last name, full name, alternate spellings
   ```csv
   Sarah Kellen,9.0,Confirmed match
   Kellen,9.0,Short form
   Sarah,8.0,First name only
   ```

2. **Use confidence wisely**:
   - 9-10: Confirmed matches from other documents
   - 5-7: Strong contextual evidence
   - 1-3: Common names, weak leads
   - 0: Untested/unknown

3. **Add notes for context**: Helps track why a name was added
   ```csv
   Marcinkova,5.5,Attempts were made to [NAME] and Brunel
   ```

4. **Review the statistics**:
   - Perfect (<1%): Near-exact width match
   - Excellent (<5%): Very likely match
   - Good (<10%): Possible match, investigate further

## How It Works

1. **Load PDF** at high resolution (1200 DPI)
2. **Find redactions** using computer vision (black rectangle detection)
3. **Calculate width** for each candidate name (using Times New Roman 12pt)
4. **Compare widths**: Find candidates within 30% tolerance
5. **Rank by combined score**: Width accuracy + confidence tie-breaker

## File Structure

```
unredactron/
├── unredactron.py          # Main analyzer script (run with: uv run unredactron.py)
├── candidates.csv          # Your suspect database
├── files/
│   └── EFTA00037366.pdf    # PDF to analyze
├── fonts/
│   └── times.ttf           # Times New Roman font
├── helpers/                # Helper scripts (font detection, redaction scan, artifacts, etc.)
│   ├── main.py             # Colab-style pipeline with RedactionCracker
│   ├── find_redactions.py
│   ├── detect_font.py
│   └── ...                 # See docs/README.md for full index
└── docs/                   # Detailed documentation per script
```

## Example Workflow

1. **Find a redaction** you want to identify
2. **Measure its width** (unredactron does this automatically)
3. **Add suspects** to candidates.csv with confidence scores
4. **Run the analyzer**: `uv run unredactron.py`
5. **Review results**: Top matches are shown with error percentages
6. **Refine**: Add more candidates or adjust confidence based on findings

## Advanced: Manual Width Testing

Test specific names against specific widths:

```python
from PIL import ImageFont

font = ImageFont.truetype("fonts/fonts/times.ttf", 200)  # 12pt @ 1200 DPI
name = "Marcinkova"
width = font.getlength(name)
print(f"{name}: {width:.1f}px")
```

## Troubleshooting

**No matches found:**
- Check that `candidates.csv` has entries
- Verify font path is correct
- Try lowering the tolerance in the code (change `30` to `50`)

**Poor matches:**
- Add more name variants to the CSV
- Check if document uses a different font
- Verify DPI setting (currently 1200)

**Confidence not working:**
- Ensure confidence is a number (not text)
- Higher values = higher priority (use 0-10 range)
