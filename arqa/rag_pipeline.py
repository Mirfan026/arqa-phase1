"""
ARQA Phase 1 — RAG Pipeline (Day 5)

Extracts text from building-code PDFs, splits into per-page chunks,
detects section numbers, and attaches metadata for retrieval.

Phase 1: per-page chunking with section-number DETECTION (citations).
Phase 1 (Day 6): upgrade to true section-based SPLITTING.

Author: Muhammad Irfan
"""
import re
import json
import os
from pypdf import PdfReader

# Pattern to DETECT building-code section numbers in text.
# Matches things like: 501.3.7.1.1, 7.8, 2.10, B.5, K.5
# - optional letter prefix (B, K, etc.)
# - digits separated by dots
SECTION_PATTERN = re.compile(r"\b([A-K]?\d+(?:\.\d+){0,4})\b")

def extract_pdf_chunks(pdf_path, country):
    """
    Extract text from a PDF, one chunk per page, with metadata.
import
    Args:
        pdf_path: path to the PDF file
        country:  e.g. "pakistan", "saudi_arabia", "uae"

    Returns:
        A list of chunk dicts. Each chunk:
        {
          "text": <page text>,
          "source_file": <filename>,
          "country": <country>,
          "pdf_page": <1-based page number>,
          "sections_detected": [<section numbers found on this page>]
        }
    """
    reader = PdfReader(pdf_path)
    filename = pdf_path.split("/")[-1]   # just the file name, not full path
    chunks = []

    for page_index, page in enumerate(reader.pages):
        text = page.extract_text() or ""   # "" if a page has no text
        text = text.strip()

        # Skip empty pages (covers, image-only pages)
        if not text:
            continue

        # Detect section numbers on this page (for citations)
        sections = SECTION_PATTERN.findall(text)

        chunk = {
            "text": text,
            "source_file": filename,
            "country": country,
            "pdf_page": page_index + 1,        # 1-based for humans
            "sections_detected": sections,
        }
        chunks.append(chunk)

    return chunks

def build_all_chunks():
    """
    Extract chunks from all Phase-1 ENGLISH building codes.

    Arabic codes are deferred to a later multilingual step.

    Returns:
        A combined list of chunk dicts from all English PDFs.
    """
    # (path, country) for each English code we gathered on Day 4
    english_codes = [
        ("data/building_codes/south_asia/pakistan/pakistan_green_building_code_2023.pdf", "pakistan"),
        ("data/building_codes/middle_east/saudi_arabia/saudi_sbc_201_architectural_2007.pdf", "saudi_arabia"),
        ("data/building_codes/middle_east/uae/uae_dubai_building_code_2021.pdf", "uae"),
        ("data/building_codes/middle_east/uae/uae_abu_dhabi_adibc_2013.pdf", "uae"),
    ]

    all_chunks = []
    for pdf_path, country in english_codes:
        print(f"Extracting: {pdf_path}")
        chunks = extract_pdf_chunks(pdf_path, country)
        print(f"  -> {len(chunks)} non-empty pages extracted")
        all_chunks.extend(chunks)

    print(f"\nTotal chunks from all codes: {len(all_chunks)}")
    return all_chunks

def save_chunks(chunks, output_path="data/rag_index/chunks.json"):
    """
    Save the extracted chunks to a JSON file so we don't have to
    re-extract from PDFs every time we index or test retrieval.
    """
    # Make sure the output folder exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(chunks)} chunks to {output_path}")


def load_chunks(input_path="data/rag_index/chunks.json"):
    """
    Load previously-saved chunks from JSON (fast — no PDF re-reading).
    """
    with open(input_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"Loaded {len(chunks)} chunks from {input_path}")
    return chunks


if __name__ == "__main__":
    chunks = build_all_chunks()

    # Save chunks to JSON so indexing/retrieval can load them instantly
    save_chunks(chunks)

    # Show a sample chunk so we can see the structure + metadata
    print("\n=== Sample chunk (a middle one) ===")
    sample = chunks[len(chunks) // 2]
    print(f"Source:   {sample['source_file']}")
    print(f"Country:  {sample['country']}")
    print(f"PDF page: {sample['pdf_page']}")
    print(f"Sections detected: {sample['sections_detected'][:10]}")
    print(f"Text preview: {sample['text'][:300]}")