"""
Convert PDF pages to PNG images at 300 DPI.
Run this before OCR.
Usage: python pdf_to_images.py [--volume 1]
"""

import sys
import argparse
import fitz
from pathlib import Path
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))
from config import PDFS, IMAGES_DIR, RENDER_DPI


def pdf_to_images(volume: int, dpi: int = RENDER_DPI, overwrite: bool = False, page_range: range = None):
    pdf_path = PDFS[volume]
    out_dir = IMAGES_DIR / f"v{volume}"
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    print(f"Volume {volume}: {len(doc)} pages → {out_dir}")

    mat = fitz.Matrix(dpi / 72, dpi / 72)

    for i, page in enumerate(tqdm(doc, desc=f"Vol {volume}")):
        page_num = i + 1
        if page_range and page_num not in page_range:
            continue
        out_path = out_dir / f"page_{page_num:03d}.png"
        if out_path.exists() and not overwrite:
            continue
        pix = page.get_pixmap(matrix=mat)
        pix.save(str(out_path))

    doc.close()
    print(f"Done. Images saved to {out_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--volume", type=int, choices=[1, 2, 3, 4], help="Volume number (omit for all)")
    parser.add_argument("--overwrite", action="store_true", help="Re-render existing images")
    parser.add_argument("--dpi", type=int, default=RENDER_DPI)
    parser.add_argument("--pages", type=str, help="Page range e.g. 6-8")
    args = parser.parse_args()

    page_range = None
    if args.pages:
        start, end = map(int, args.pages.split("-"))
        page_range = range(start, end + 1)

    volumes = [args.volume] if args.volume else [1, 2, 3, 4]
    for v in volumes:
        pdf_to_images(v, dpi=args.dpi, overwrite=args.overwrite, page_range=page_range)
