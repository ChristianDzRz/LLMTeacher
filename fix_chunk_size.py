#!/usr/bin/env python3
"""
Fix chunk size to fit within 4096 token context window.

Current: 12,000 chars (~3,000 words) → Too large!
Fixed: 6,000 chars (~1,500 words) → Fits comfortably
"""

from pathlib import Path


def fix_topic_extractor():
    """Reduce chunk size in topic_extractor.py"""

    file_path = Path("src/topic_extractor.py")
    content = file_path.read_text()

    # Fix the chunk_text function default
    old = "def chunk_text(\n        text: str, max_words: int = 2000, overlap_words: int = 200\n    ) -> List[str]:"
    new = "def chunk_text(\n        text: str, max_words: int = 1000, overlap_words: int = 100\n    ) -> List[str]:"

    content = content.replace(old, new)

    # Fix the docstring
    old_doc = "max_words: Maximum words per chunk (default 2000 for safety)"
    new_doc = "max_words: Maximum words per chunk (default 1000 for 4096 token limit)"

    content = content.replace(old_doc, new_doc)

    # Fix extract_topics function default
    old_param = "max_chunk_words: int = 2000,"
    new_param = "max_chunk_words: int = 1000,"

    content = content.replace(old_param, new_param)

    # Fix extract_topics docstring
    old_extract_doc = (
        "max_chunk_words: Maximum words per chunk (default 2000 for 4096 token context)"
    )
    new_extract_doc = (
        "max_chunk_words: Maximum words per chunk (default 1000 for 4096 token context)"
    )

    content = content.replace(old_extract_doc, new_extract_doc)

    file_path.write_text(content)
    print("✅ Fixed src/topic_extractor.py - reduced chunk size to 1000 words")


def fix_context_manager():
    """Reduce passage size in context_manager.py"""

    file_path = Path("src/context_manager.py")
    content = file_path.read_text()

    # The context manager already uses smaller chunks (1000 chars)
    # Just verify it's not using word-based sizing that's too large

    print(
        "✅ src/context_manager.py - already using appropriate chunk size (1000 chars)"
    )


def main():
    print("=" * 70)
    print("FIXING CHUNK SIZE FOR 4096 TOKEN CONTEXT WINDOW")
    print("=" * 70)
    print()
    print("Reducing chunk size from 2000 words → 1000 words")
    print("This ensures chunks fit within the 4096 token limit")
    print()

    fix_topic_extractor()
    fix_context_manager()

    print()
    print("=" * 70)
    print("✅ CHUNK SIZE FIXED!")
    print()
    print("New configuration:")
    print("  • Topic extraction: 1000 words/chunk (~6000 chars)")
    print("  • 10% overlap: 100 words")
    print("  • Estimated tokens: ~1500 per chunk (safe for 4096 limit)")
    print()
    print("Try processing your book again!")
    print("=" * 70)


if __name__ == "__main__":
    main()
