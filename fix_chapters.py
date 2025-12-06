#!/usr/bin/env python3
"""
Quick script to disable buggy chapter detection.
Run this to patch the files automatically.
"""

import sys
from pathlib import Path


def fix_document_parser():
    """Disable chapter extraction in document_parser.py"""

    parser_file = Path("src/document_parser.py")

    if not parser_file.exists():
        print(f"❌ File not found: {parser_file}")
        return False

    content = parser_file.read_text()

    # Find and comment out chapter extraction
    old_code = """                # Extract TOC chapters first
                toc_chapters = DocumentParser.extract_toc_chapters(result["content"])
                print(f"Found {len(toc_chapters)} chapters in TOC")

                # Extract chapters from content using TOC
                result["chapters"] = DocumentParser.extract_chapters_from_text(
                    result["content"],
                    toc_chapters=toc_chapters if toc_chapters else None,
                )"""

    new_code = """                # DISABLED: Chapter extraction creates too many false positives
                # Extract TOC chapters first
                # toc_chapters = DocumentParser.extract_toc_chapters(result["content"])
                # print(f"Found {len(toc_chapters)} chapters in TOC")

                # Extract chapters from content using TOC
                # result["chapters"] = DocumentParser.extract_chapters_from_text(
                #     result["content"],
                #     toc_chapters=toc_chapters if toc_chapters else None,
                # )
                result["chapters"] = []
                print("Chapter auto-detection disabled, using simple chunking")"""

    if old_code in content:
        content = content.replace(old_code, new_code)

        # Also fix the PyPDF2 fallback section
        old_code2 = """                # Extract TOC chapters first
                toc_chapters = DocumentParser.extract_toc_chapters(result["content"])
                print(f"Found {len(toc_chapters)} chapters in TOC")

                # Extract chapters from content using TOC
                result["chapters"] = DocumentParser.extract_chapters_from_text(
                    result["content"],
                    toc_chapters=toc_chapters if toc_chapters else None,
                )"""

        content = content.replace(old_code2, new_code)

        parser_file.write_text(content)
        print("✅ Fixed src/document_parser.py - chapter detection disabled")
        return True
    else:
        print(
            "⚠️ Could not find the code to replace. File may already be fixed or modified."
        )
        return False


def fix_topic_extractor():
    """Add chapter count validation in topic_extractor.py"""

    extractor_file = Path("src/topic_extractor.py")

    if not extractor_file.exists():
        print(f"❌ File not found: {extractor_file}")
        return False

    content = extractor_file.read_text()

    old_code = """        # Use chapters if available, otherwise fall back to chunking
        if chapters and len(chapters) > 0:
            print(
                f"Book has {len(chapters)} chapters/sections, processing by chapter..."
            )
            return self._extract_topics_from_chapters(chapters, book_title)"""

    new_code = """        # DISABLED: Automatic chapter detection creates too many false positives
        # Only use chapters if there are 3-20 of them (reasonable chapter count)
        if chapters and 3 <= len(chapters) <= 20:
            print(
                f"Book has {len(chapters)} chapters, processing by chapter..."
            )
            return self._extract_topics_from_chapters(chapters, book_title)
        elif chapters and len(chapters) > 20:
            print(
                f"⚠️ Too many chapters detected ({len(chapters)}), likely false positives. Using simple chunking instead."
            )"""

    if old_code in content:
        content = content.replace(old_code, new_code)
        extractor_file.write_text(content)
        print("✅ Fixed src/topic_extractor.py - added chapter count validation")
        return True
    else:
        print("⚠️ Could not find the code to replace in topic_extractor.py")
        return False


def main():
    print("=" * 70)
    print("FIXING CHAPTER DETECTION BUG")
    print("=" * 70)
    print()

    # Check we're in the right directory
    if not Path("src").exists():
        print("❌ Error: src/ directory not found")
        print("Please run this script from the book-learning-app directory")
        sys.exit(1)

    print("This will disable automatic chapter detection to fix the bug")
    print("where 361 chapters are detected, creating 205,835 chunks.")
    print()

    # Apply fixes
    fix1 = fix_document_parser()
    fix2 = fix_topic_extractor()

    print()
    print("=" * 70)

    if fix1 or fix2:
        print("✅ FIXES APPLIED!")
        print()
        print("Test the fix by running:")
        print("  uv run python compare_chunking.py")
        print()
        print("You should now see ~70 chunks instead of 205,835")
    else:
        print("⚠️ No changes made. Files may already be fixed.")

    print("=" * 70)


if __name__ == "__main__":
    main()
