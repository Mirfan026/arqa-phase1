"""
ARQA Phase 1 — Day 5
Quick experiment: extract text from one building-code PDF
to confirm pypdf can read it and see what the raw text looks like.

This is an exploration script, not part of the arqa/ package.
"""

from pypdf import PdfReader

# Path to one of our real building codes (Pakistan — current edition)
PDF_PATH = "data/building_codes/south_asia/pakistan/pakistan_green_building_code_2023.pdf"

# Open the PDF
reader = PdfReader(PDF_PATH)

print(f"PDF opened: {PDF_PATH}")
print(f"Total pages: {len(reader.pages)}")

# Sample some middle pages where actual rules live (not front-matter)
sample_pages = [30, 50, 80, 120]
print("\n--- Sample text from rule-bearing pages ---\n")
for page_num in sample_pages:
    if page_num < len(reader.pages):
        page = reader.pages[page_num]
        text = page.extract_text()
        print(f"===== PAGE {page_num + 1} =====")
        print(text[:700])  # first 700 characters
        print()