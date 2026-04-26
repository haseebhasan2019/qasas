"""
OCR Arabic pages using Google Gemini Vision API (free tier).
Free tier: 15 requests/min, 1500 requests/day — sufficient for all 384 pages.

Setup:
  1. Go to https://aistudio.google.com/apikey and create a free API key
  2. Add to .env: GEMINI_API_KEY=your_key_here

Usage:
  python ocr.py --volume 1
  python ocr.py --volume 1 --pages 1-10
  python ocr.py --volume 1 --page 5
  python ocr.py  (all volumes)
"""

import sys
import time
import json
import argparse
from pathlib import Path
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))
from config import IMAGES_DIR, RAW_TEXT_DIR, GEMINI_API_KEY, GEMINI_MODEL, OCR_RATE_LIMIT_DELAY, LOW_TASHKEEL_THRESHOLD

from google import genai
from google.genai import types

PROMPT = """Transcribe all Arabic text from this page exactly as written.

Critical requirements:
- Preserve EVERY diacritical mark (tashkeel): fatha (َ), kasra (ِ), damma (ُ), tanwin forms (ً ٍ ٌ), shadda (ّ), sukoon (ْ)
- Maintain paragraph breaks using blank lines
- Output ONLY the Arabic text — no translation, no commentary, no page numbers
- If a line is decorative or blank, skip it"""


def count_tashkeel(text: str) -> tuple[int, int]:
    arabic = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    tashkeel = sum(1 for c in text if '\u064B' <= c <= '\u065F' or
                   '\u0610' <= c <= '\u061A' or '\u06D6' <= c <= '\u06DC')
    return arabic, tashkeel


def ocr_page(client: genai.Client, image_path: Path, retries: int = 3) -> str:
    image_bytes = image_path.read_bytes()
    error_attempts = 0  # only counts non-rate-limit errors toward the retry limit

    while True:
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                    PROMPT,
                ],
            )
            return response.text.strip()
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower() or "rate" in err.lower():
                # Use the retry delay from the API response if present, else default to 60s
                import re as _re
                match = _re.search(r'retryDelay.*?(\d+)s', err)
                wait = int(match.group(1)) + 5 if match else 60
                print(f"\nRate limited. Waiting {wait}s...")
                time.sleep(wait)
                # Don't count rate limit waits as error attempts — just retry
            else:
                error_attempts += 1
                if error_attempts >= retries:
                    raise
                print(f"\nError (attempt {error_attempts}): {e}. Retrying in 5s...")
                time.sleep(5)


def process_volume(volume: int, page_range: range | None = None, overwrite: bool = False):
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_api_key_here":
        print("ERROR: Set GEMINI_API_KEY in .env file.")
        print("Get a free key at: https://aistudio.google.com/apikey")
        sys.exit(1)

    client = genai.Client(api_key=GEMINI_API_KEY)

    images_dir = IMAGES_DIR / f"v{volume}"
    text_dir = RAW_TEXT_DIR / f"v{volume}"
    text_dir.mkdir(parents=True, exist_ok=True)

    image_files = sorted(images_dir.glob("page_*.png"))
    if not image_files:
        print(f"No images found in {images_dir}. Run pdf_to_images.py first.")
        sys.exit(1)

    if page_range:
        image_files = [f for f in image_files
                       if int(f.stem.split("_")[1]) in page_range]

    failed_pages = []
    blank_pages = []
    low_tashkeel_pages = []

    print(f"Volume {volume}: processing {len(image_files)} pages with Gemini ({GEMINI_MODEL})")

    for img_path in tqdm(image_files, desc=f"Vol {volume}"):
        page_num = int(img_path.stem.split("_")[1])
        out_path = text_dir / f"page_{page_num:03d}.txt"

        if out_path.exists() and not overwrite:
            continue

        try:
            text = ocr_page(client, img_path)
            out_path.write_text(text, encoding="utf-8")

            if not text.strip():
                print(f"\nWARNING: Page {page_num} came back blank — may need re-OCR with --overwrite")
                blank_pages.append(page_num)
                continue

            arabic, tashkeel = count_tashkeel(text)
            density = (tashkeel / arabic * 100) if arabic > 0 else 0

            if arabic > 20 and density < LOW_TASHKEEL_THRESHOLD:
                low_tashkeel_pages.append({
                    "page": page_num,
                    "arabic_chars": arabic,
                    "tashkeel_chars": tashkeel,
                    "density": round(density, 2)
                })

            # Respect free tier rate limit: ~15 req/min
            time.sleep(OCR_RATE_LIMIT_DELAY)

        except Exception as e:
            print(f"\nFailed page {page_num}: {e}")
            failed_pages.append(page_num)

    report = {
        "volume": volume,
        "total_pages_attempted": len(image_files),
        "failed_pages": failed_pages,
        "blank_pages": blank_pages,
        "low_tashkeel_pages": low_tashkeel_pages,
    }
    report_path = text_dir / "quality_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nDone. Failed: {len(failed_pages)}, Blank: {len(blank_pages)}, Low tashkeel: {len(low_tashkeel_pages)}")
    if failed_pages:
        print(f"  Failed pages: {failed_pages}")
    if blank_pages:
        print(f"  Blank pages (re-run with --overwrite): {blank_pages}")
    if low_tashkeel_pages:
        print(f"  Low tashkeel (check manually): {[p['page'] for p in low_tashkeel_pages]}")
    print(f"Quality report: {report_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--volume", type=int, choices=[1, 2, 3, 4],
                        help="Volume number (omit for all)")
    parser.add_argument("--pages", type=str, help="Page range e.g. 1-20")
    parser.add_argument("--page", type=int, help="Single page number")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    page_range = None
    if args.page:
        page_range = range(args.page, args.page + 1)
    elif args.pages:
        start, end = map(int, args.pages.split("-"))
        page_range = range(start, end + 1)

    volumes = [args.volume] if args.volume else [1, 2, 3, 4]
    for v in volumes:
        process_volume(v, page_range=page_range, overwrite=args.overwrite)
