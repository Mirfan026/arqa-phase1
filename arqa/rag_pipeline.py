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

# Heading regex (see Day 6 design):
#   ^          start of a line (MULTILINE)
#   [A-K]?     optional letter prefix (Dubai's K.5.3.2, B.6...)
#   \d+        digits
#   (?:\.\d+)+ at least one ".digits" group  -> kills bare page numbers
#   \s+        space(s)
#   [A-Z][a-z] start of a Capitalized title  -> kills measurements / ALL-CAPS
HEADING_RE = re.compile(r"^([A-K]?\d+(?:\.\d+)+)\s+[A-Z][a-z]", re.MULTILINE)


def split_page_into_sections(page_chunk):
    """
    Split one per-page chunk into finer section-chunks.

    Uses HEADING_RE to find where each section starts, then slices
    the page text between consecutive headings. Each resulting chunk
    keeps the page's metadata + the detected section number.

    If a page has no detectable headings, it is returned unchanged
    as a single chunk (so we never lose content).
    """
    text = page_chunk["text"]

    # Find all heading matches and where they start in the text
    matches = list(HEADING_RE.finditer(text))

    # No headings on this page -> keep the whole page as one chunk
    if not matches:
        return [{
            "text": text,
            "source_file": page_chunk["source_file"],
            "country": page_chunk["country"],
            "pdf_page": page_chunk["pdf_page"],
            "section": None,
        }]

    sections = []

    # Text before the first heading (page header, leftover from prev section)
    # is attached to nothing — we skip it to avoid noise. (It's usually
    # page labels like "MEANS OF EGRESS SBC 201 2007 8/13".)

    for i, match in enumerate(matches):
        start = match.start()
        # This section runs until the next heading (or end of page)
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        section_text = text[start:end].strip()
        section_number = match.group(1)   # the captured number, e.g. "8.8.1"

        sections.append({
            "text": section_text,
            "source_file": page_chunk["source_file"],
            "country": page_chunk["country"],
            "pdf_page": page_chunk["pdf_page"],
            "section": section_number,
        })

    return sections

def build_section_chunks(page_chunks_path="data/rag_index/chunks.json",
                          output_path="data/rag_index/section_chunks.json"):
    """
    Load the cached per-page chunks, split each into section-chunks,
    and save the finer-grained result.

    Returns the list of section-chunks.
    """
    page_chunks = load_chunks(page_chunks_path)

    section_chunks = []
    pages_with_headings = 0

    for page_chunk in page_chunks:
        sections = split_page_into_sections(page_chunk)
        # A page "had headings" if it produced sections WITH a section number
        if any(s["section"] is not None for s in sections):
            pages_with_headings += 1
        section_chunks.extend(sections)

    # Save the section-chunks
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(section_chunks, f, ensure_ascii=False, indent=2)

    # Report what happened
    print(f"Pages processed:        {len(page_chunks)}")
    print(f"Pages with headings:    {pages_with_headings}")
    print(f"Section-chunks created: {len(section_chunks)}")
    with_section = sum(1 for c in section_chunks if c["section"] is not None)
    print(f"  - with section number: {with_section}")
    print(f"  - whole-page (no heading detected): {len(section_chunks) - with_section}")
    print(f"Saved to {output_path}")

    return section_chunks

if __name__ == "__main__":
    # Day 6: build section-chunks from the cached page-chunks.
    section_chunks = build_section_chunks()

    # Collect samples first
    samples = [c for c in section_chunks if c["section"] is not None][:3]
    fallbacks = [c for c in section_chunks if c["section"] is None][:2]

    # Print clean section-chunks
    print("\n=== Sample section-chunks ===")
    for s in samples:
        print(f"\n[{s['country']} | {s['source_file']} p.{s['pdf_page']} | "
              f"section {s['section']}]")
        preview = " ".join(s["text"].split())[:250]
        print(f"  {preview}")

    # Print whole-page fallbacks
    print("\n=== Sample whole-page fallbacks (no heading detected) ===")
    for s in fallbacks:
        print(f"\n[{s['country']} | {s['source_file']} p.{s['pdf_page']} | no section]")
        preview = " ".join(s["text"].split())[:250]
        print(f"  {preview}")