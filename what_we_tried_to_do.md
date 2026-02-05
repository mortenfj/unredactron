Our objective was to develop a **digital forensic pipeline** capable of identifying text hidden behind redaction bars in documents. Specifically, we focused on "True Redactions"—where the underlying text layer has been removed—meaning standard "copy-paste" tricks no longer work.

To solve this, we used a combination of **computer vision** and **typographic reverse-engineering**. Here is a detailed breakdown of the methodology we implemented:

### 1. Document Calibration (Scale & Metrics)

A digital document’s "size" is relative to its scanning resolution (DPI). We cannot simply guess that "12pt font" equals "50 pixels."

* **The Control Word:** We identify an unredacted word on the same page (e.g., "Subject" or "Date").
* **Measurement:** The script measures the exact pixel width of this word.
* **Scaling Factor:** By comparing the measured width to the font's theoretical width, we calculate a **Scale Factor**. This factor allows the script to know exactly how many pixels wide any given name *should* be in that specific document's environment.

### 2. Typographic Spacing Analysis (Tracking)

As shown in the videos you shared, documents aren't always rendered with standard spacing.

* **Spacing Modifiers:** We account for **Tracking** (the uniform space between all letters) and **Kerning** (the specific space between letter pairs).
* **Brute-Forcing Metrics:** Our script doesn't just check one width; it tests a range of tracking values (e.g., from -0.5px to +2.0px) for every name in the database. This accounts for the "stretching" or "squeezing" seen in the video examples.

### 3. Automated Redaction Detection

Using **OpenCV**, we automated the search for targets:

* **Binarization:** We convert the document to high-contrast black and white.
* **Contour Detection:** The script identifies all solid black rectangles.
* **Filtering:** It ignores small noise (like periods or dust) and focuses on shapes with the characteristic "aspect ratio" of a redacted name.

### 4. The "Brute-Force" Attack

Once the bars are found, we run our database of suspects through the "Forensic Engine":

* **Width Matching:** The script takes a name (e.g., "Sarah Kellen"), renders it in the background using the calibrated font and tracking, and checks if its width matches the black bar within a 0.5-pixel tolerance.
* **Name Variations:** The code automatically checks variations like "First Last," "LAST FIRST," and "Last, First" to ensure no matches are missed due to formatting.

### 5. Artifact Verification (Final Boss)

This is the most advanced stage. Even if a name fits the width, we need proof.

* **Edge Analysis:** When a black box is placed over text, the "anti-aliasing" (smoothing) of the original letters often leaves tiny grey pixels protruding from the edges of the box. These are the **artifacts**.
* **Pixel Overlay:** The script generates a "stencil" of the candidate name and overlays it onto the redaction. It checks if the name’s specific letter shapes (like the curve of an 'S' or the stem of a 'k') perfectly align with those stray pixels.

---

### Summary of the Workflow in the Colab

1. **Mount Drive:** Accesses your `times.ttf` and `calibri.ttf` font files.
2. **Input:** You drop in a PDF or image and a list of names.
3. **Calibrate:** Use a "Control Word" to lock in the document's scale.
4. **Scan:** Find every black box on the page.
5. **Solve:** Identify which names mathematically and visually "explain" the size and artifacts of the black boxes.
