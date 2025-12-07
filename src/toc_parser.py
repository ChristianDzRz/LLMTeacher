"""
Table of Contents parser for extracting chapter structure from user-pasted TOC.
"""

import re
from typing import Dict, List, Optional


class TOCParser:
    """Parse table of contents text into structured chapter data."""

    @staticmethod
    def parse(toc_text: str) -> List[Dict]:
        """
        Parse table of contents text into a list of chapters.

        Handles various formats:
        - "Chapter 1: Introduction ............ 1"
        - "1. Introduction"
        - "Chapter One - Getting Started"
        - "Part I: Fundamentals"
        - "1 Introduction 15"
        - Simple numbered lists

        Args:
            toc_text: Raw table of contents text

        Returns:
            List of chapter dictionaries with 'title' and optional 'page'
        """
        if not toc_text or not toc_text.strip():
            return []

        lines = toc_text.strip().split("\n")
        chapters = []

        for line in lines:
            chapter = TOCParser._parse_line(line)
            if chapter:
                chapters.append(chapter)

        # Filter out likely non-chapter entries
        chapters = TOCParser._filter_chapters(chapters)

        return chapters

    @staticmethod
    def _parse_line(line: str) -> Optional[Dict]:
        """Parse a single TOC line into a chapter dict."""
        line = line.strip()

        if not line:
            return None

        # Skip common non-chapter entries
        skip_patterns = [
            r"^(preface|foreword|acknowledgment|about|copyright|index|appendix|glossary|bibliography|references)$",
            r"^table of contents$",
            r"^contents$",
            r"^part\s+[ivxlc]+$",  # Roman numeral parts without title
        ]

        line_lower = line.lower()
        for pattern in skip_patterns:
            if re.match(pattern, line_lower):
                return None

        # Try various patterns to extract chapter title and page number

        # Pattern 1: "Chapter X: Title .... page" or "Chapter X - Title"
        match = re.match(
            r"^(?:chapter\s+)?(\d+|[ivxlc]+)[:\.\-\s]+(.+?)(?:\.{2,}|\s{2,})(\d+)\s*$",
            line,
            re.IGNORECASE,
        )
        if match:
            title = match.group(2).strip()
            page = int(match.group(3))
            return {"title": title, "page": page, "number": match.group(1)}

        # Pattern 1b: "Chapter X: Title" without page number
        match = re.match(
            r"^(?:chapter\s+)(\d+|[ivxlc]+)[:\.\-\s]+(.+?)$",
            line,
            re.IGNORECASE,
        )
        if match:
            title = match.group(2).strip()
            title = re.sub(r"\.{2,}\s*\d*\s*$", "", title).strip()
            return {"title": title, "page": None, "number": match.group(1)}

        # Pattern 2: "X. Title" or "X Title"
        match = re.match(r"^(\d+)[\.\)\s]+(.+?)(?:\.{2,}|\s{2,})(\d+)?\s*$", line)
        if match:
            title = match.group(2).strip()
            page = int(match.group(3)) if match.group(3) else None
            return {"title": title, "page": page, "number": match.group(1)}

        # Pattern 3: Simple "X. Title" without page
        match = re.match(r"^(\d+)[\.\)\s]+(.+)$", line)
        if match:
            title = match.group(2).strip()
            # Remove trailing dots or page numbers
            title = re.sub(r"\.{2,}\s*\d*\s*$", "", title).strip()
            return {"title": title, "page": None, "number": match.group(1)}

        # Pattern 4: "Part X: Title"
        match = re.match(
            r"^part\s+(\d+|[ivxlc]+)[:\.\-\s]+(.+?)(?:\.{2,}|\s{2,})(\d+)?\s*$",
            line,
            re.IGNORECASE,
        )
        if match:
            title = f"Part {match.group(1)}: {match.group(2).strip()}"
            page = int(match.group(3)) if match.group(3) else None
            return {"title": title, "page": page, "number": match.group(1)}

        # Pattern 5: Title with page number at end (no chapter number)
        match = re.match(r"^(.+?)(?:\.{2,}|\s{3,})(\d+)\s*$", line)
        if match:
            title = match.group(1).strip()
            if len(title) > 3:  # Avoid matching just numbers
                page = int(match.group(2))
                return {"title": title, "page": page, "number": None}

        # Pattern 6: Just a title (if it looks like a chapter)
        if len(line) > 5 and not line.isdigit():
            # Check if it looks like a chapter title
            chapter_keywords = [
                "introduction",
                "chapter",
                "getting started",
                "basic",
                "advanced",
                "conclusion",
                "summary",
            ]
            if any(kw in line.lower() for kw in chapter_keywords) or re.match(
                r"^[A-Z]", line
            ):
                return {"title": line, "page": None, "number": None}

        return None

    @staticmethod
    def _filter_chapters(chapters: List[Dict]) -> List[Dict]:
        """Filter out entries that don't look like real chapters."""
        if not chapters:
            return []

        # If we have too few entries, keep them all
        if len(chapters) <= 3:
            return chapters

        # Filter out very short titles
        filtered = [ch for ch in chapters if len(ch["title"]) > 3]

        # If we have numbered chapters, prefer those
        numbered = [ch for ch in filtered if ch.get("number")]
        if len(numbered) >= 3:
            return numbered

        return filtered

    @staticmethod
    def get_chapter_titles(toc_text: str) -> List[str]:
        """
        Get just the chapter titles from TOC text.

        Args:
            toc_text: Raw table of contents text

        Returns:
            List of chapter title strings
        """
        chapters = TOCParser.parse(toc_text)
        return [ch["title"] for ch in chapters]

    @staticmethod
    def match_content_to_chapters(content: str, chapters: List[Dict]) -> List[Dict]:
        """
        Match book content to parsed chapters.

        Args:
            content: Full book text content
            chapters: List of chapter dicts from parse()

        Returns:
            List of chapter dicts with 'content' field added
        """
        if not chapters or not content:
            return chapters

        result = []
        content_lower = content.lower()

        for i, chapter in enumerate(chapters):
            title = chapter["title"]

            # Find chapter start position
            start_pos = TOCParser._find_chapter_start(content, content_lower, title)

            if start_pos == -1:
                # Chapter not found in content, skip it
                continue

            # Find end position (start of next chapter or end of content)
            end_pos = len(content)
            for next_chapter in chapters[i + 1 :]:
                next_start = TOCParser._find_chapter_start(
                    content, content_lower, next_chapter["title"]
                )
                if next_start > start_pos:
                    end_pos = next_start
                    break

            # Extract chapter content
            chapter_content = content[start_pos:end_pos].strip()

            if len(chapter_content) > 100:  # Only include substantial chapters
                result.append({**chapter, "content": chapter_content})

        return result

    @staticmethod
    def _find_chapter_start(content: str, content_lower: str, title: str) -> int:
        """Find the starting position of a chapter in the content."""
        title_lower = title.lower()

        # Try exact match first
        pos = content_lower.find(title_lower)
        if pos != -1:
            return pos

        # Try matching first few words
        words = title_lower.split()
        if len(words) >= 2:
            partial = " ".join(words[:3])
            pos = content_lower.find(partial)
            if pos != -1:
                return pos

        # Try fuzzy match with key words
        key_words = [w for w in words if len(w) > 4]
        for word in key_words:
            pos = content_lower.find(word)
            if pos != -1:
                # Verify this looks like a chapter heading
                context = content[max(0, pos - 50) : pos + len(word) + 50]
                if re.search(r"(chapter|\n\n|\n\s*\n)", context.lower()):
                    return pos

        return -1


if __name__ == "__main__":
    # Test the parser
    sample_toc = """
    Chapter 1: Introduction to SQL ............ 1
    Chapter 2: Basic Queries .................. 25
    Chapter 3: Filtering Data ................. 52
    4. Joining Tables ......................... 89
    5. Aggregation Functions .................. 120
    Advanced Topics ........................... 150
    """

    chapters = TOCParser.parse(sample_toc)
    print("Parsed chapters:")
    for ch in chapters:
        print(f"  - {ch['title']} (page: {ch.get('page')})")
