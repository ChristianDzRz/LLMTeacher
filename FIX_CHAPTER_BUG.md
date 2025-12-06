# Quick Fix for Chapter Detection Bug

## The Problem

The automatic chapter detection is finding way too many "chapters" (361 for a 380-page book), which then gets split into 205,835 chunks. This makes processing extremely slow.

## Quick Fix (Option 1): Disable Chapter Detection

Edit `src/topic_extractor.py` line 91-95:

**Change from:**
```python
# Use chapters if available, otherwise fall back to chunking
if chapters and len(chapters) > 0:
    print(
        f"Book has {len(chapters)} chapters/sections, processing by chapter..."
    )
    return self._extract_topics_from_chapters(chapters, book_title)
```

**Change to:**
```python
# DISABLED: Automatic chapter detection creates too many false positives
# Only use chapters if there are 3-20 of them (reasonable chapter count)
if chapters and 3 <= len(chapters) <= 20:
    print(
        f"Book has {len(chapters)} chapters, processing by chapter..."
    )
    return self._extract_topics_from_chapters(chapters, book_title)
elif chapters and len(chapters) > 20:
    print(
        f"⚠️ Too many chapters detected ({len(chapters)}), likely false positives. Using simple chunking instead."
    )
```

## Quick Fix (Option 2): Disable Chapter Extraction Completely

Edit `src/document_parser.py` at the end of `parse_pdf()` function (around line 270):

**Change from:**
```python
# Extract TOC chapters first
toc_chapters = DocumentParser.extract_toc_chapters(result["content"])
print(f"Found {len(toc_chapters)} chapters in TOC")

# Extract chapters from content using TOC
result["chapters"] = DocumentParser.extract_chapters_from_text(
    result["content"],
    toc_chapters=toc_chapters if toc_chapters else None,
)
```

**Change to:**
```python
# DISABLED: Chapter extraction creates too many false positives
# Extract TOC chapters first
# toc_chapters = DocumentParser.extract_toc_chapters(result["content"])
# print(f"Found {len(toc_chapters)} chapters in TOC")

# Extract chapters from content using TOC
# result["chapters"] = DocumentParser.extract_chapters_from_text(
#     result["content"],
#     toc_chapters=toc_chapters if toc_chapters else None,
# )
result["chapters"] = []  # Disable automatic chapter detection
print("Chapter auto-detection disabled, using simple chunking")
```

Do the same for the PyPDF2 fallback section (around line 300).

## Expected Result After Fix

```
⏳ Parsing book...
Chapter auto-detection disabled, using simple chunking
✅ Book parsed successfully!
Book is large (113,155 words), processing in chunks...
Processing 70 chunks with 200-word overlap...  # Much better!
```

## Apply the Fix

Run this after editing:
```bash
uv run python compare_chunking.py
```

You should see ~70 chunks instead of 205,835!

## Better Long-term Solution

Add a manual TOC input feature where users can paste chapter titles and page ranges. This would be more accurate than automatic detection.
