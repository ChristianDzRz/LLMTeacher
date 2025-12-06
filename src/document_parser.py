"""
Document parser for extracting text from PDF and EPUB files.
"""

import os
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional

import pdfplumber
import PyPDF2
from ebooklib import ITEM_DOCUMENT, epub


class HTMLTextExtractor(HTMLParser):
    """Extract plain text from HTML content."""

    def __init__(self):
        super().__init__()
        self.text = []
        self.skip_tags = {"script", "style"}
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag

    def handle_data(self, data):
        if self.current_tag not in self.skip_tags:
            text = data.strip()
            if text:
                self.text.append(text)

    def get_text(self):
        return " ".join(self.text)


class DocumentParser:
    """Parse PDF and EPUB documents to extract text content."""

    @staticmethod
    def extract_toc_chapters(text: str) -> List[str]:
        """
        Extract chapter titles from table of contents.

        Args:
            text: Full book text

        Returns:
            List of chapter titles found in TOC
        """
        import re

        lines = text.split("\n")
        toc_chapters = []
        in_toc = False

        for i, line in enumerate(lines):
            line_lower = line.lower().strip()

            # Detect start of TOC
            if "table of contents" in line_lower or "contents" == line_lower:
                in_toc = True
                continue

            # Detect end of TOC (usually starts with "Chapter 1" or "Preface" content)
            if in_toc and (
                line_lower.startswith("preface")
                or line_lower.startswith("chapter 1")
                or line_lower.startswith("1.")
            ):
                # Check if this looks like actual content (long paragraph) vs TOC entry
                if len(line.split()) > 20:  # Actual content, not TOC entry
                    break

            if in_toc and line.strip():
                # Look for chapter patterns in TOC
                # Common patterns: "Chapter 1: Title", "1. Title", "Title .... 23"

                # Remove page numbers (sequences of dots followed by numbers)
                cleaned = re.sub(r"\.{2,}\s*\d+\s*$", "", line).strip()
                cleaned = re.sub(
                    r"\s+\d+\s*$", "", cleaned
                ).strip()  # Just numbers at end

                # Check if it looks like a chapter title
                if len(cleaned) > 3 and len(cleaned) < 100:
                    # Skip common non-chapter entries
                    skip = [
                        "preface",
                        "foreword",
                        "acknowledgment",
                        "about the author",
                        "copyright",
                        "index",
                        "appendix",
                        "glossary",
                    ]
                    if not any(s in cleaned.lower() for s in skip):
                        toc_chapters.append(cleaned)

        return toc_chapters

    @staticmethod
    def _extract_chapters_from_toc(
        text: str, toc_chapters: List[str], max_chapter_words: int
    ) -> List[Dict[str, str]]:
        """
        Extract chapter content using TOC chapter titles as boundaries.

        Args:
            text: Full book text
            toc_chapters: List of chapter titles from TOC
            max_chapter_words: Maximum words per chapter

        Returns:
            List of chapter dictionaries
        """
        import re

        chapters = []
        text_lines = text.split("\n")

        # For each TOC chapter, find where it appears in the text
        for i, chapter_title in enumerate(toc_chapters):
            # Clean the chapter title for matching
            clean_title = chapter_title.strip()

            # Find the start of this chapter in the text
            chapter_start_idx = None
            for line_idx, line in enumerate(text_lines):
                # Fuzzy match: check if chapter title appears in line
                if clean_title.lower() in line.lower():
                    # Make sure it's not just a TOC reference (short line = likely heading)
                    if len(line.split()) < 20:
                        chapter_start_idx = line_idx
                        break

            if chapter_start_idx is None:
                continue

            # Find the end (start of next chapter or end of book)
            chapter_end_idx = len(text_lines)
            if i + 1 < len(toc_chapters):
                next_title = toc_chapters[i + 1].strip()
                for line_idx in range(chapter_start_idx + 10, len(text_lines)):
                    line = text_lines[line_idx]
                    if next_title.lower() in line.lower():
                        if len(line.split()) < 20:
                            chapter_end_idx = line_idx
                            break

            # Extract chapter content
            chapter_lines = text_lines[chapter_start_idx:chapter_end_idx]
            chapter_content = "\n".join(chapter_lines).strip()

            # Skip if too short
            if len(chapter_content.split()) < 100:
                continue

            # Split if too long
            if len(chapter_content.split()) > max_chapter_words:
                words = chapter_content.split()
                for part_num, j in enumerate(
                    range(0, len(words), max_chapter_words), 1
                ):
                    chunk = " ".join(words[j : j + max_chapter_words])
                    chapters.append(
                        {"title": f"{clean_title} (Part {part_num})", "content": chunk}
                    )
            else:
                chapters.append({"title": clean_title, "content": chapter_content})

        return chapters

    @staticmethod
    def extract_chapters_from_text(
        text: str, max_chapter_words: int = 1200, toc_chapters: List[str] = None
    ) -> List[Dict[str, str]]:
        """
        Extract chapters from text based on TOC or heading patterns.

        Args:
            text: Full book text
            max_chapter_words: Maximum words per chapter (splits large chapters, default 1200 for 4096 token limit)
            toc_chapters: Optional list of chapter titles from TOC

        Returns:
            List of chapter dictionaries with title and content
        """
        import re

        # If we have TOC chapters, use those to find chapter boundaries
        if toc_chapters and len(toc_chapters) > 0:
            return DocumentParser._extract_chapters_from_toc(
                text, toc_chapters, max_chapter_words
            )

        # Otherwise fall back to pattern matching

        lines = text.split("\n")
        chapters = []
        current_chapter = None
        current_content = []

        # Common chapter heading patterns (conservative to avoid false positives)
        chapter_patterns = [
            r"^Chapter\s+\d+",
            r"^CHAPTER\s+\d+",
            r"^\d+\.\s+[A-Z][a-z]+",  # "1. Introduction" (require lowercase to avoid single letters)
            r"^PART\s+[IVX\d]+",
            r"^[A-Z][A-Z\s]{15,60}$",  # ALL CAPS titles (15-60 chars, longer to avoid headers)
        ]

        for line in lines:
            line_stripped = line.strip()

            # Check if this line matches a chapter heading pattern
            is_chapter_heading = False
            if line_stripped and len(line_stripped) < 100:
                for pattern in chapter_patterns:
                    if re.match(pattern, line_stripped, re.IGNORECASE):
                        is_chapter_heading = True
                        break

            if is_chapter_heading:
                # Save previous chapter
                if current_chapter and current_content:
                    content_text = "\n".join(current_content).strip()

                    # Split large chapters
                    if len(content_text.split()) > max_chapter_words:
                        # Split into sub-sections
                        words = content_text.split()
                        for i in range(0, len(words), max_chapter_words):
                            chunk = " ".join(words[i : i + max_chapter_words])
                            chapters.append(
                                {
                                    "title": f"{current_chapter} (Part {i // max_chapter_words + 1})",
                                    "content": chunk,
                                }
                            )
                    else:
                        chapters.append(
                            {"title": current_chapter, "content": content_text}
                        )

                # Start new chapter
                current_chapter = line_stripped
                current_content = []
            else:
                # Add to current chapter
                if line_stripped:
                    current_content.append(line_stripped)

        # Add last chapter
        if current_chapter and current_content:
            content_text = "\n".join(current_content).strip()
            if len(content_text.split()) > max_chapter_words:
                words = content_text.split()
                for i in range(0, len(words), max_chapter_words):
                    chunk = " ".join(words[i : i + max_chapter_words])
                    chapters.append(
                        {
                            "title": f"{current_chapter} (Part {i // max_chapter_words + 1})",
                            "content": chunk,
                        }
                    )
            else:
                chapters.append({"title": current_chapter, "content": content_text})

        # If no chapters detected, split by page breaks or sections
        if not chapters:
            # Fallback: split into chunks
            paragraphs = text.split("\n\n")
            current_content = []
            current_words = 0
            section_num = 1

            for para in paragraphs:
                para_words = len(para.split())

                if current_words + para_words > max_chapter_words and current_content:
                    chapters.append(
                        {
                            "title": f"Section {section_num}",
                            "content": "\n\n".join(current_content),
                        }
                    )
                    section_num += 1
                    current_content = [para]
                    current_words = para_words
                else:
                    current_content.append(para)
                    current_words += para_words

            if current_content:
                chapters.append(
                    {
                        "title": f"Section {section_num}",
                        "content": "\n\n".join(current_content),
                    }
                )

        return chapters

    @staticmethod
    def parse_pdf(file_path: str) -> Dict[str, any]:
        """
        Parse PDF file and extract text content.

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary containing:
            - title: Book title (from metadata or filename)
            - content: Full text content
            - page_count: Number of pages
            - metadata: Additional metadata
            - chapters: List of chapter dictionaries
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        result = {
            "title": file_path.stem,
            "content": "",
            "page_count": 0,
            "metadata": {},
            "chapters": [],
        }

        # Try pdfplumber first (better text extraction)
        try:
            with pdfplumber.open(file_path) as pdf:
                result["page_count"] = len(pdf.pages)

                text_parts = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)

                result["content"] = "\n\n".join(text_parts)

                # DISABLED: Chapter extraction creates too many false positives
                # Extract TOC chapters first
                # toc_chapters = DocumentParser.extract_toc_chapters(result["content"])
                # print(f"Found {len(toc_chapters)} chapters in TOC")

                # Extract chapters from content using TOC
                # result["chapters"] = DocumentParser.extract_chapters_from_text(
                #     result["content"],
                #     toc_chapters=toc_chapters if toc_chapters else None,
                # )
                result["chapters"] = []
                print("Chapter auto-detection disabled, using simple chunking")

        except Exception as e:
            # Fallback to PyPDF2 if pdfplumber fails
            print(f"pdfplumber failed, falling back to PyPDF2: {e}")

            with open(file_path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                result["page_count"] = len(pdf_reader.pages)

                # Extract metadata
                if pdf_reader.metadata:
                    result["metadata"] = {
                        "author": pdf_reader.metadata.get("/Author", ""),
                        "creator": pdf_reader.metadata.get("/Creator", ""),
                        "producer": pdf_reader.metadata.get("/Producer", ""),
                        "subject": pdf_reader.metadata.get("/Subject", ""),
                    }

                    # Use title from metadata if available
                    if "/Title" in pdf_reader.metadata:
                        result["title"] = pdf_reader.metadata["/Title"]

                # Extract text from all pages
                text_parts = []
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)

                result["content"] = "\n\n".join(text_parts)

                # DISABLED: Chapter extraction creates too many false positives
                # Extract TOC chapters first
                # toc_chapters = DocumentParser.extract_toc_chapters(result["content"])
                # print(f"Found {len(toc_chapters)} chapters in TOC")

                # Extract chapters from content using TOC
                # result["chapters"] = DocumentParser.extract_chapters_from_text(
                #     result["content"],
                #     toc_chapters=toc_chapters if toc_chapters else None,
                # )
                result["chapters"] = []
                print("Chapter auto-detection disabled, using simple chunking")

        return result

    @staticmethod
    def parse_epub(file_path: str) -> Dict[str, any]:
        """
        Parse EPUB file and extract text content.

        Args:
            file_path: Path to EPUB file

        Returns:
            Dictionary containing:
            - title: Book title
            - content: Full text content
            - chapters: List of chapter titles (if available)
            - metadata: Additional metadata
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        book = epub.read_epub(file_path)

        result = {
            "title": file_path.stem,
            "content": "",
            "chapters": [],
            "metadata": {},
        }

        # Extract metadata
        title = book.get_metadata("DC", "title")
        if title:
            result["title"] = title[0][0]

        author = book.get_metadata("DC", "creator")
        if author:
            result["metadata"]["author"] = author[0][0]

        language = book.get_metadata("DC", "language")
        if language:
            result["metadata"]["language"] = language[0][0]

        # Extract text content from all document items
        text_parts = []
        html_extractor = HTMLTextExtractor()

        for item in book.get_items():
            if item.get_type() == ITEM_DOCUMENT:
                # Extract text from HTML content
                html_content = item.get_content().decode("utf-8", errors="ignore")

                html_extractor.text = []  # Reset for each item
                html_extractor.feed(html_content)
                text = html_extractor.get_text()

                if text:
                    text_parts.append(text)

                    # Try to identify chapter title (usually in first heading)
                    # This is a simple heuristic
                    lines = text.split("\n")
                    if lines:
                        potential_title = lines[0].strip()
                        if len(potential_title) < 100:  # Likely a title if short
                            result["chapters"].append(potential_title)

        result["content"] = "\n\n".join(text_parts)

        return result

    @staticmethod
    def parse(file_path: str) -> Dict[str, any]:
        """
        Parse document (auto-detect format from extension).

        Args:
            file_path: Path to document file

        Returns:
            Parsed document data
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()

        if extension == ".pdf":
            return DocumentParser.parse_pdf(file_path)
        elif extension == ".epub":
            return DocumentParser.parse_epub(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")

    @staticmethod
    def get_text_statistics(content: str) -> Dict[str, int]:
        """
        Get basic statistics about the text content.

        Args:
            content: Text content

        Returns:
            Dictionary with word_count, char_count, etc.
        """
        words = content.split()

        return {
            "word_count": len(words),
            "char_count": len(content),
            "char_count_no_spaces": len(content.replace(" ", "")),
            "line_count": len(content.split("\n")),
        }


if __name__ == "__main__":
    # Simple test
    import sys

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(f"Parsing: {file_path}")

        result = DocumentParser.parse(file_path)

        print(f"\nTitle: {result['title']}")
        print(f"Content length: {len(result['content'])} characters")

        stats = DocumentParser.get_text_statistics(result["content"])
        print(f"Word count: {stats['word_count']}")
        print(
            f"Pages/Chapters: {result.get('page_count', len(result.get('chapters', [])))}"
        )

        print(f"\nFirst 500 characters:")
        print(result["content"][:500])
    else:
        print("Usage: python document_parser.py <path_to_pdf_or_epub>")
