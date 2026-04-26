"""
Assemble per-page raw text files into structured JSON.
Detects chapter boundaries based on short centered lines (headings).

Usage:
  python build_json.py --volume 1
  python build_json.py  (all volumes)
"""

import sys
import re
import json
import argparse
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent))
from config import RAW_TEXT_DIR, JSON_DIR, PDFS


def is_likely_heading(line: str) -> bool:
    """Heuristic: a heading is a short Arabic line (< 50 chars) with no sentence punctuation."""
    stripped = line.strip()
    if not stripped:
        return False
    # Ignore pure page numbers (Arabic-Indic or Western digits only)
    if re.match(r'^[\d٠-٩\s]+$', stripped):
        return False
    # Count Arabic letters (not digits/punctuation)
    arabic_chars = sum(1 for c in stripped if '\u0621' <= c <= '\u064A')
    if arabic_chars < 3:
        return False
    # Short lines that are mostly Arabic letters
    if len(stripped) < 50 and arabic_chars / len(stripped) > 0.5:
        # No mid-sentence punctuation
        if not any(c in stripped for c in ['،', '؛', '؟', '!']):
            return True
    return False


def parse_page_into_paragraphs(text: str) -> list[str]:
    """Split page text into paragraphs (blank line separated)."""
    paragraphs = []
    current = []

    for line in text.splitlines():
        if line.strip():
            current.append(line.strip())
        else:
            if current:
                paragraphs.append("\n".join(current))
                current = []

    if current:
        paragraphs.append("\n".join(current))

    return [p for p in paragraphs if p.strip()]


def build_volume_json(volume: int) -> dict:
    text_dir = RAW_TEXT_DIR / f"v{volume}"
    text_files = sorted(text_dir.glob("page_*.txt"))

    if not text_files:
        print(f"No text files found for volume {volume}. Run 03_ocr_claude_vision.py first.")
        return {}

    chapters = []
    current_chapter = None
    chapter_num = 0

    pages_data = []

    for txt_path in text_files:
        page_num = int(txt_path.stem.split("_")[1])
        text = txt_path.read_text(encoding="utf-8").strip()

        if not text:
            continue

        paragraphs = parse_page_into_paragraphs(text)

        # Detect chapter boundaries: first paragraph is a heading
        if paragraphs and is_likely_heading(paragraphs[0]):
            chapter_num += 1
            if current_chapter:
                chapters.append(current_chapter)

            current_chapter = {
                "chapter_number": chapter_num,
                "title": paragraphs[0],
                "pages": []
            }
            # Rest of the page goes into this chapter
            remaining = paragraphs[1:]
        else:
            remaining = paragraphs

        if current_chapter is None:
            # Pages before first detected chapter
            chapter_num = 1
            current_chapter = {
                "chapter_number": chapter_num,
                "title": "مقدمة",
                "pages": []
            }

        if remaining:
            page_entry = {
                "page_number": len(current_chapter["pages"]) + 1,
                "original_pdf_page": page_num,
                "paragraphs": [
                    {
                        "id": f"v{volume}_c{chapter_num}_op{page_num}_p{i+1}",
                        "text": para
                    }
                    for i, para in enumerate(remaining)
                ]
            }
            current_chapter["pages"].append(page_entry)

    if current_chapter:
        chapters.append(current_chapter)

    result = {
        "volume": volume,
        "title": "قصص النبيين",
        "title_transliterated": "Qasas un Nabiyeen",
        "chapters": chapters,
        "metadata": {
            "source_pdf": PDFS[volume].name,
            "extraction_method": "claude-vision",
            "build_date": str(date.today()),
            "total_pdf_pages": len(text_files),
            "total_chapters": len(chapters),
        }
    }

    return result


def print_chapter_summary(data: dict):
    print(f"\nVolume {data['volume']} — Chapter Summary:")
    for ch in data["chapters"]:
        page_count = len(ch["pages"])
        print(f"  Ch {ch['chapter_number']:2d}: {ch['title'][:50]} ({page_count} pages)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--volume", type=int, choices=[1, 2, 3, 4], help="Volume (omit for all)")
    args = parser.parse_args()

    # JSON is written to pipeline/output/json/. The files in web/data/ are
    # symlinks pointing here, so the site picks up changes automatically.
    JSON_DIR.mkdir(parents=True, exist_ok=True)
    volumes = [args.volume] if args.volume else [1, 2, 3, 4]

    for v in volumes:
        print(f"\nBuilding JSON for Volume {v}...")
        data = build_volume_json(v)
        if not data:
            continue

        out_path = JSON_DIR / f"volume_{v}.json"
        out_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"Saved: {out_path}")
        print_chapter_summary(data)
