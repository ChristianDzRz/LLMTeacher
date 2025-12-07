"""
Chapter-based book processor for generating structured learning materials.

This module processes books chapter by chapter, creating:
1. A book structure file with chapter overviews
2. Individual chapter files with detailed topics and key points
"""

import json
import re
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from src.document_parser import DocumentParser
from src.llm_client import LLMClient
from src.toc_parser import TOCParser


class ChapterProcessor:
    """Process books chapter by chapter for better context management."""

    def __init__(self, llm_client: LLMClient = None):
        """
        Initialize chapter processor.

        Args:
            llm_client: LLM client instance
        """
        self.llm_client = llm_client or LLMClient()
        self.progress_file = None
        self.book_folder_name = None

    def _write_progress(self, current: int, total: int, message: str = ""):
        """Write progress to temporary file for frontend polling."""
        if not self.progress_file:
            return

        try:
            progress = int((current / total) * 100) if total > 0 else 0
            progress_data = {
                "progress": progress,
                "current": current,
                "total": total,
                "message": message,
                "book_folder": self.book_folder_name,  # Add book folder name
            }
            print(
                f"[DEBUG] Writing progress: {progress}%, folder: {self.book_folder_name}, message: {message}"
            )
            with open(self.progress_file, "w") as f:
                json.dump(progress_data, f)
        except Exception as e:
            print(f"[DEBUG] Error writing progress: {e}")
            pass

    def _generate_book_overview(self, book_title: str, chapters: List[Dict]) -> Dict:
        """
        Generate overall book structure with chapter summaries.

        Args:
            book_title: Title of the book
            chapters: List of chapter dictionaries with 'title' and 'content'

        Returns:
            Dictionary with book overview and chapter summaries
        """
        # Create a summary of all chapters
        chapters_text = "\n\n".join(
            [
                f"Chapter {i + 1}: {ch.get('title', '')}\n{ch.get('content', '')[:500]}..."
                for i, ch in enumerate(chapters[:10])  # First 10 chapters for overview
            ]
        )

        overview_prompt = f"""Analyze the book "{book_title}" and provide a structured overview.

Chapters:
{chapters_text}

Create a JSON response with:
1. book_summary: 2-3 sentence overview of the entire book
2. chapters: Array of chapter objects with:
   - chapter_number: number
   - title: chapter title
   - brief_description: 1-2 sentences about what this chapter covers
   - key_concepts: 3-5 main concepts/topics (array of strings)

Format EXACTLY as JSON:
{{
  "book_summary": "...",
  "total_chapters": {len(chapters)},
  "chapters": [
    {{
      "chapter_number": 1,
      "title": "...",
      "brief_description": "...",
      "key_concepts": ["concept1", "concept2", "concept3"]
    }}
  ]
}}

Respond ONLY with valid JSON."""

        response = self.llm_client.simple_prompt(
            overview_prompt, temperature=0.4, max_tokens=8000
        )

        # Debug logging
        print(f"\n{'=' * 60}")
        print("LLM Response for book overview:")
        print(f"{'=' * 60}")
        print(response[:500] if len(response) > 500 else response)
        if len(response) > 500:
            print(f"... (truncated, total length: {len(response)} chars)")
        print(f"{'=' * 60}\n")

        # Parse JSON response - try multiple strategies
        overview = None

        # Strategy 1: Find JSON block between curly braces
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(0)
                # Clean up common issues
                json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
                overview = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON (strategy 1): {e}")

        # Strategy 2: Try to find JSON in code blocks
        if not overview:
            code_block_match = re.search(
                r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL
            )
            if code_block_match:
                try:
                    json_str = code_block_match.group(1)
                    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
                    overview = json.loads(json_str)
                    print("Successfully parsed JSON from code block")
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON (strategy 2): {e}")

        # Strategy 3: Strip everything except JSON-like content
        if not overview:
            try:
                # Remove markdown, extra text, etc.
                cleaned = re.sub(r"^[^{]*", "", response)  # Remove before first {
                cleaned = re.sub(r"[^}]*$", "", cleaned)  # Remove after last }
                json_str = re.sub(r",\s*([}\]])", r"\1", cleaned)
                overview = json.loads(json_str)
                print("Successfully parsed JSON (strategy 3)")
            except (json.JSONDecodeError, Exception) as e:
                print(f"Failed to parse JSON (strategy 3): {e}")

        if overview:
            # Ensure all chapters are included (not just first 10)
            if len(overview.get("chapters", [])) < len(chapters):
                for i in range(len(overview.get("chapters", [])), len(chapters)):
                    overview["chapters"].append(
                        {
                            "chapter_number": i + 1,
                            "title": chapters[i].get("title", f"Chapter {i + 1}"),
                            "brief_description": "Additional chapter content",
                            "key_concepts": [],
                        }
                    )
            return overview
        else:
            # If all parsing fails, print full response and raise error
            print("\n" + "=" * 60)
            print("FULL LLM RESPONSE (parsing failed):")
            print("=" * 60)
            print(response)
            print("=" * 60 + "\n")
            raise ValueError(
                f"Could not parse book overview. Response length: {len(response)} chars. Check logs for full response."
            )

    def _extract_chapter_topics(
        self, chapter_title: str, chapter_content: str, chapter_number: int
    ) -> Dict:
        """
        Extract detailed topics and key points from a chapter.

        Args:
            chapter_title: Chapter title
            chapter_content: Chapter content
            chapter_number: Chapter number

        Returns:
            Dictionary with topics and key points
        """
        # Limit content to avoid token limits (use first ~3000 words)
        words = chapter_content.split()
        if len(words) > 3000:
            content_sample = " ".join(words[:3000]) + "..."
        else:
            content_sample = chapter_content

        topics_prompt = f"""Analyze Chapter {chapter_number}: "{chapter_title}"

Content:
{content_sample}

Extract the key learning topics and concepts. Focus on:
1. Main topics that students should understand
2. Key points and important concepts
3. Practical applications or examples
4. Prerequisites or foundational knowledge needed

Since the model has internet access, focus on identifying WHAT to learn, not explaining everything in detail.
The model can search for additional information when teaching these topics.

Format as JSON:
{{
  "chapter_number": {chapter_number},
  "title": "{chapter_title}",
  "topics": [
    {{
      "topic_number": 1,
      "title": "Topic title",
      "description": "What this topic covers (1-2 sentences)",
      "key_points": ["point1", "point2", "point3"],
      "importance": "High|Medium|Low",
      "suggested_search_queries": ["query to find more info", "another query"]
    }}
  ],
  "prerequisites": ["prerequisite knowledge needed"],
  "summary": "1-2 sentence chapter summary"
}}

Respond ONLY with valid JSON. Include 3-8 topics per chapter."""

        response = self.llm_client.simple_prompt(
            topics_prompt, temperature=0.4, max_tokens=6000
        )

        # Debug logging
        print(f"\n{'=' * 60}")
        print(f"LLM Response for chapter {chapter_number}:")
        print(f"{'=' * 60}")
        print(response[:500] if len(response) > 500 else response)
        if len(response) > 500:
            print(f"... (truncated, total length: {len(response)} chars)")
        print(f"{'=' * 60}\n")

        # Parse JSON response - try multiple strategies
        chapter_data = None

        # Strategy 1: Find JSON block between curly braces
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(0)
                # Clean up common issues
                json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
                chapter_data = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON (strategy 1): {e}")

        # Strategy 2: Try to find JSON in code blocks
        if not chapter_data:
            code_block_match = re.search(
                r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL
            )
            if code_block_match:
                try:
                    json_str = code_block_match.group(1)
                    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
                    chapter_data = json.loads(json_str)
                    print("Successfully parsed JSON from code block")
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON (strategy 2): {e}")

        # Strategy 3: Strip everything except JSON-like content
        if not chapter_data:
            try:
                # Remove markdown, extra text, etc.
                cleaned = re.sub(r"^[^{]*", "", response)  # Remove before first {
                cleaned = re.sub(r"[^}]*$", "", cleaned)  # Remove after last }
                json_str = re.sub(r",\s*([}\]])", r"\1", cleaned)
                chapter_data = json.loads(json_str)
                print("Successfully parsed JSON (strategy 3)")
            except (json.JSONDecodeError, Exception) as e:
                print(f"Failed to parse JSON (strategy 3): {e}")

        if chapter_data:
            # Add chapter content (truncated for storage efficiency)
            chapter_data["content_preview"] = " ".join(words[:200])
            return chapter_data
        else:
            # If all parsing fails, print full response and raise error
            print("\n" + "=" * 60)
            print(f"FULL LLM RESPONSE for chapter {chapter_number} (parsing failed):")
            print("=" * 60)
            print(response)
            print("=" * 60 + "\n")
            raise ValueError(
                f"Could not parse chapter topics. Response length: {len(response)} chars. Check logs for full response."
            )

    @staticmethod
    def _create_book_folder_name(
        title: str, author: str = None, year: str = None
    ) -> str:
        """
        Create a nice folder name from book metadata.

        Format: Title - Author (Year) or just Title if no author/year

        Args:
            title: Book title
            author: Book author
            year: Publication year

        Returns:
            Clean folder name
        """
        # Clean title - remove special chars but keep spaces
        clean_title = re.sub(r"[^\w\s-]", "", title).strip()
        clean_title = re.sub(
            r"\s+", " ", clean_title
        )  # Normalize multiple spaces to single space

        # Build folder name
        folder_name = clean_title

        if author:
            clean_author = re.sub(r"[^\w\s-]", "", author).strip()
            clean_author = re.sub(r"\s+", " ", clean_author)  # Normalize spaces
            folder_name += f" - {clean_author}"

        if year:
            clean_year = re.sub(r"[^\d]", "", str(year))[:4]  # Get first 4 digits
            if clean_year:
                folder_name += f" ({clean_year})"

        return folder_name

    def process_book(
        self,
        book_path: str,
        output_dir: str = None,
        toc_text: str = None,
    ) -> Dict:
        """
        Process a book chapter by chapter.

        Creates a folder structure:
        {Title - Author (Year)}/
            structure.json
            chapter_1.json
            chapter_2.json
            ...

        Args:
            book_path: Path to book file
            output_dir: Output directory
            toc_text: Optional table of contents text

        Returns:
            Dictionary with processing results
        """
        import config

        base_output_dir = Path(output_dir or config.PROCESSED_FOLDER)
        base_output_dir.mkdir(parents=True, exist_ok=True)

        # Set up progress file and clear any old progress
        self.progress_file = (
            Path(tempfile.gettempdir()) / "book_processing_progress.json"
        )

        # Clear old progress file to start fresh
        if self.progress_file.exists():
            try:
                self.progress_file.unlink()
                print("Cleared old progress file")
            except Exception as e:
                print(f"Warning: Could not clear old progress file: {e}")

        print(f"Parsing book: {book_path}")
        book_data = DocumentParser.parse(book_path)

        # Extract metadata for folder naming
        metadata = book_data.get("metadata", {})
        author = metadata.get("author", metadata.get("creator", None))
        year = metadata.get("year", metadata.get("creation_date", None))

        # Create book folder with nice name
        book_folder_name = self._create_book_folder_name(
            book_data["title"], author, year
        )
        self.book_folder_name = book_folder_name  # Store for progress tracking
        output_dir = base_output_dir / book_folder_name
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"Created book folder: {book_folder_name}")

        # Get chapters
        chapters = []
        if toc_text:
            print("\n" + "=" * 60)
            print("CHAPTER DETECTION: Using user-provided Table of Contents")
            print("=" * 60)
            parsed_toc = TOCParser.parse(toc_text)
            if parsed_toc:
                print(f"✓ Parsed {len(parsed_toc)} chapters from TOC")
                for i, ch in enumerate(parsed_toc[:5], 1):  # Show first 5
                    print(f"  {i}. {ch.get('title', 'Unknown')}")
                if len(parsed_toc) > 5:
                    print(f"  ... and {len(parsed_toc) - 5} more")

                chapters = TOCParser.match_content_to_chapters(
                    book_data["content"], parsed_toc
                )
                print(f"✓ Matched {len(chapters)} chapters with content")

        if not chapters:
            print("\n" + "=" * 60)
            print("CHAPTER DETECTION: Attempting auto-detection")
            print("=" * 60)
            chapters = book_data.get("chapters", [])
            if chapters:
                print(f"✓ Auto-detected {len(chapters)} chapters")
                for i, ch in enumerate(chapters[:5], 1):  # Show first 5
                    title = ch.get("title", "Unknown")
                    word_count = len(ch.get("content", "").split())
                    print(f"  {i}. {title} ({word_count} words)")
                if len(chapters) > 5:
                    print(f"  ... and {len(chapters) - 5} more")
            else:
                print("✗ No chapters auto-detected")

        # Only fall back to single chapter if truly no chapters found
        print("\n" + "=" * 60)
        if not chapters:
            # If no chapters detected, treat whole book as single chapter
            print("⚠ FALLBACK: Processing entire book as single chapter")
            print(f"Book: {book_data['title']}")
            print(f"Total words: {len(book_data['content'].split())}")
            print("=" * 60)
            chapters = [
                {
                    "title": book_data["title"],
                    "content": book_data["content"],
                    "number": 1,
                }
            ]
        elif len(chapters) == 1:
            print(f"⚠ WARNING: Only 1 chapter detected")
            print(f"Chapter: {chapters[0].get('title', 'Unknown')}")
            print(f"Words: {len(chapters[0].get('content', '').split())}")
            print(f"This might be incorrect. Consider providing a table of contents.")
            print("=" * 60)
        else:
            print(f"✓ FINAL: Processing {len(chapters)} chapters")
            print("=" * 60)

        # Generate book overview
        print("Generating book structure overview...")
        self._write_progress(0, len(chapters) + 1, "Analyzing book structure")

        try:
            book_overview = self._generate_book_overview(book_data["title"], chapters)
        except Exception as e:
            print(f"Warning: Could not generate book overview: {e}")
            print("Continuing with minimal overview...")
            # Create a minimal overview instead of failing completely
            book_overview = {
                "book_summary": f"Learning guide for {book_data['title']}",
                "total_chapters": len(chapters),
                "chapters": [
                    {
                        "chapter_number": i + 1,
                        "title": ch.get("title", f"Chapter {i + 1}"),
                        "brief_description": "Chapter content",
                        "key_concepts": [],
                    }
                    for i, ch in enumerate(chapters)
                ],
            }

        # Process each chapter
        chapter_files = []
        for i, chapter in enumerate(chapters, 1):
            chapter_title = chapter.get("title", f"Chapter {i}")
            print(f"Processing chapter {i}/{len(chapters)}: {chapter_title}")
            self._write_progress(i, len(chapters) + 1, f"Processing: {chapter_title}")

            try:
                chapter_data = self._extract_chapter_topics(
                    chapter_title, chapter.get("content", ""), i
                )

                # Save individual chapter file (simple naming within book folder)
                chapter_file = output_dir / f"chapter_{i}.json"

                with open(chapter_file, "w", encoding="utf-8") as f:
                    json.dump(chapter_data, f, indent=2, ensure_ascii=False)

                chapter_files.append(
                    {
                        "chapter_number": i,
                        "file": chapter_file.name,
                        "title": chapter_title,
                        "topic_count": len(chapter_data.get("topics", [])),
                    }
                )

                print(
                    f"  Saved chapter {i} with {len(chapter_data.get('topics', []))} topics"
                )

            except Exception as e:
                print(f"  ERROR processing chapter {i}: {e}")
                # Create minimal chapter data as fallback with at least one topic
                chapter_data = {
                    "chapter_number": i,
                    "title": chapter_title,
                    "topics": [
                        {
                            "topic_number": 1,
                            "title": chapter_title,
                            "description": f"Study the content of {chapter_title}",
                            "key_points": ["Review the chapter content"],
                            "importance": "High",
                            "suggested_search_queries": [],
                        }
                    ],
                    "prerequisites": [],
                    "summary": f"Chapter {i}: {chapter_title}",
                    "content_preview": chapter.get("content", "")[:200],
                }

                chapter_file = output_dir / f"chapter_{i}.json"
                with open(chapter_file, "w", encoding="utf-8") as f:
                    json.dump(chapter_data, f, indent=2, ensure_ascii=False)

                chapter_files.append(
                    {
                        "chapter_number": i,
                        "file": chapter_file.name,
                        "title": chapter_title,
                        "topic_count": 0,
                    }
                )
                print(f"  Created minimal chapter file for chapter {i}")
                continue

        # Create book structure file (simple naming within book folder)
        structure_file = output_dir / "structure.json"

        book_structure = {
            "book_info": {
                "title": book_data["title"],
                "file_name": Path(book_path).name,
                "metadata": book_data.get("metadata", {}),
                "word_count": len(book_data["content"].split()),
                "page_count": book_data.get("page_count", 0),
                "chapter_count": len(chapters),
                "folder_name": book_folder_name,  # Store folder name for reference
            },
            "overview": book_overview,
            "chapters": chapter_files,
            "processing_date": str(Path(structure_file).stat().st_mtime)
            if structure_file.exists()
            else None,
        }

        with open(structure_file, "w", encoding="utf-8") as f:
            json.dump(book_structure, f, indent=2, ensure_ascii=False)

        print(f"\nSaved book structure to: {structure_file}")
        print(f"Book folder: {book_folder_name}")
        print(f"Created {len(chapter_files)} chapter files")

        self._write_progress(len(chapters) + 1, len(chapters) + 1, "Complete!")

        return book_structure


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        book_path = sys.argv[1]
        processor = ChapterProcessor()
        result = processor.process_book(book_path)
        print(f"\nProcessed: {result['book_info']['title']}")
        print(f"Chapters: {result['book_info']['chapter_count']}")
    else:
        print("Usage: python chapter_processor.py <path_to_book>")
