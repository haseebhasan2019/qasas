# Qasas un Nabiyeen — قصص النبيين

A digital reader for *Qasas un Nabiyeen* (Stories of the Prophets), a classical Arabic text in four volumes. The project includes a PDF-to-JSON processing pipeline and a clean Arabic web reader with full tashkeel (diacritical marks).

**Live site:** https://haseebhasan2019.github.io/qasas

---

## Project Structure

```
qasas/
├── pipeline/       # PDF → JSON processing scripts
│   ├── pdf_to_images.py    # Convert scanned PDF pages to PNG (300 DPI)
│   ├── ocr.py              # OCR each page image via Gemini Vision API
│   ├── build_json.py       # Assemble per-page text into structured JSON
│   ├── config.py           # Shared paths and settings
│   └── requirements.txt
├── docs/           # Web reader (served via GitHub Pages)
│   ├── index.html          # Volume selection page
│   ├── reader.html         # Chapter/page reader
│   ├── css/main.css
│   ├── js/
│   │   ├── reader.js
│   │   └── tashkeel.js
│   └── data/               # Processed JSON volumes
├── pdfs/           # Source PDF files (not committed)
└── plan.txt        # Pipeline design notes
```

---

## Pipeline

The pipeline converts scanned Arabic PDFs into structured JSON for the web reader.

```
PDF → PNG images → OCR text (per page) → structured JSON → website
```

**Steps:**

1. `pdf_to_images.py` — Convert each PDF page to a 300 DPI PNG image
2. `ocr.py` — Send page images to Gemini Vision API; transcribe all Arabic text and diacritics exactly
3. `build_json.py` — Assemble per-page text files into a single JSON file structured by volume → chapter → page → paragraph

### Setup

```bash
cd pipeline
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_key_here
```

---

## Web Reader

A static Arabic web reader with right-to-left layout, using the [Scheherazade New](https://fonts.google.com/specimen/Scheherazade+New) font for clear tashkeel rendering.

- Volume selection landing page
- Chapter and page navigation
- Full tashkeel preservation

To run locally, serve the `docs/` directory with any static file server:

```bash
cd docs
python -m http.server 8000
```

---

## Data Format

Each volume is stored as a JSON file in `docs/data/`:

```json
{
  "volume": 1,
  "chapters": [
    {
      "title": "...",
      "pages": [
        {
          "page": 1,
          "paragraphs": ["..."]
        }
      ]
    }
  ]
}
```
