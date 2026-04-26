import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

ROOT = Path(__file__).parent.parent
PDFS_DIR = ROOT / "pdfs"
OUTPUT_DIR = Path(__file__).parent / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
RAW_TEXT_DIR = OUTPUT_DIR / "raw_text"
JSON_DIR = OUTPUT_DIR / "json"

PDFS = {
    1: PDFS_DIR / "Qasas-Un-Nabiyeen-1.pdf",
    2: PDFS_DIR / "Qasas-Un-Nabiyeen-2.pdf",
    3: PDFS_DIR / "Qasas-Un-Nabiyeen-3.pdf",
    4: PDFS_DIR / "Qasas-Un-Nabiyeen-4.pdf",
}

# DPI for page rendering (300 is high quality, 150 is faster/smaller)
RENDER_DPI = 300

# Gemini model to use (free tier)
GEMINI_MODEL = "models/gemini-2.5-flash"

# Seconds to wait between OCR requests to respect free tier rate limit (~15 req/min)
OCR_RATE_LIMIT_DELAY = 4

# Pages with tashkeel density below this % are flagged for manual review
LOW_TASHKEEL_THRESHOLD = 5.0

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
