"""
Topic extractor for analyzing books and generating learning plans.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from src.document_parser import DocumentParser
from src.llm_client import LLMClient, PromptTemplates
from src.text_splitter import ImprovedTextSplitter


class TopicExtractor:
    """Extract key learning topics from book content."""

    def __init__(self, llm_client: LLMClient = None):
        """
        Initialize topic extractor.

        Args:
            llm_client: LLM client instance (creates new one if not provided)
        """
        self.llm_client = llm_client or LLMClient()

    @staticmethod
    def chunk_text(
        text: str, max_words: int = 2457, overlap_words: int = 245
    ) -> List[str]:
        """
        Split text into chunks with overlap for better context preservation.

        Uses improved text splitting based on best practices:
        - 10% overlap (default) maintains context across chunks
        - Respects paragraph boundaries
        - Character-based sizing for precision

        Args:
            text: Full text content
            max_words: Maximum words per chunk (default 1000 for 4096 token limit)
            overlap_words: Words to overlap between chunks (default 200, 10%)

        Returns:
            List of text chunks with overlap
        """
        # Convert word-based sizing to character-based (approximate)
        # Assume average word length of 5 characters + 1 space = 6 chars per word
        chunk_size = max_words * 6
        overlap_size = overlap_words * 6

        # Use improved text splitter with overlap
        splitter = ImprovedTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap_size,
            separator="\n\n",
        )

        return splitter.split_text(text)

    def extract_topics(
        self,
        book_content: str,
        book_title: str,
        chapters: List[Dict] = None,
        max_chunk_words: int = 2457,
    ) -> List[Dict]:
        """
        Extract key learning topics from book content.

        Args:
            book_content: Full book text
            book_title: Title of the book
            chapters: Optional list of chapter dictionaries with 'title' and 'content'
            max_chunk_words: Maximum words per chunk (default 1000 for 4096 token context)

        Returns:
            List of topic dictionaries with structure:
            [
                {
                    "topic_number": 1,
                    "title": "Topic Title",
                    "description": "Description",
                    "importance": "High"
                },
                ...
            ]
        """
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

        # Check if book needs to be chunked
        word_count = len(book_content.split())

        if word_count > max_chunk_words:
            print(f"Book is large ({word_count} words), processing in chunks...")
            return self._extract_topics_from_chunks(
                book_content, book_title, max_chunk_words
            )
        else:
            return self._extract_topics_single(book_content, book_title)

    def _extract_topics_from_chapters(
        self, chapters: List[Dict], book_title: str
    ) -> List[Dict]:
        """
        Extract topics from chapters while preserving chapter context.

        Strategy:
        1. Combine chapters into larger chunks (to reduce API calls)
        2. Extract topics from combined chunks
        3. Create unified learning plan
        """
        # Filter out non-content chapters (TOC, copyright, etc.)
        skip_keywords = [
            "table of contents",
            "copyright",
            "preface",
            "about the author",
            "revision history",
            "by ",
            "acknowledgment",
            "foreword",
            "index",
        ]

        content_chapters = []
        for chapter in chapters:
            title_lower = chapter.get("title", "").lower()
            # Skip if title matches skip keywords or chapter is very short
            if (
                any(kw in title_lower for kw in skip_keywords)
                or len(chapter.get("content", "").split()) < 100
            ):
                continue
            content_chapters.append(chapter)

        print(f"Found {len(content_chapters)} content chapters after filtering")

        # If we have too many chapters (likely false positives), use chunking instead
        if len(content_chapters) > 30:
            print(
                f"Too many chapters detected ({len(content_chapters)}), falling back to automatic chunking..."
            )
            # Combine all content and use chunk-based processing
            full_content = "\n\n".join(
                [ch.get("content", "") for ch in content_chapters]
            )
            return self._extract_topics_from_chunks(full_content, book_title, 1200)

        # Combine chapters into larger chunks to reduce API calls
        # Target: ~1000-1200 words per chunk (safe for 4096 token context)
        combined_chunks = []
        current_chunk = {"chapters": [], "content": [], "word_count": 0}

        for chapter in content_chapters:
            chapter_content = chapter.get("content", "")
            chapter_words = len(chapter_content.split())

            # If adding this chapter would exceed limit, save current chunk
            if (
                current_chunk["word_count"] + chapter_words > 1200
                and current_chunk["content"]
            ):
                combined_chunks.append(current_chunk)
                current_chunk = {"chapters": [], "content": [], "word_count": 0}

            current_chunk["chapters"].append(chapter.get("title", ""))
            current_chunk["content"].append(chapter_content)
            current_chunk["word_count"] += chapter_words

        # Add remaining chunk
        if current_chunk["content"]:
            combined_chunks.append(current_chunk)

        print(
            f"Processing {len(content_chapters)} chapters in {len(combined_chunks)} combined chunks..."
        )

        all_topics = []

        for i, chunk_data in enumerate(combined_chunks, 1):
            chunk_title = " + ".join(chunk_data["chapters"][:3])
            if len(chunk_data["chapters"]) > 3:
                chunk_title += f" + {len(chunk_data['chapters']) - 3} more"

            chunk_content = "\n\n".join(chunk_data["content"])

            print(
                f"  Processing chunk {i}/{len(combined_chunks)}: {chunk_title} ({chunk_data['word_count']} words)"
            )

            try:
                # Extract topics from this combined chunk
                chunk_topics = self._extract_topics_single(
                    chunk_content, f"{book_title}"
                )

                all_topics.extend(chunk_topics)
            except Exception as e:
                print(f"    ERROR processing chunk {i}: {e}")
                # Continue with other chunks instead of failing completely
                continue

        # Merge topics from all chunks
        print(f"Merging topics from {len(combined_chunks)} chunks...")
        final_topics = self._merge_topics(all_topics, book_title)

        return final_topics

    def _extract_topics_single(
        self, book_content: str, book_title: str, retry_count: int = 0
    ) -> List[Dict]:
        """Extract topics from a single chunk of content."""
        prompt = PromptTemplates.topic_extraction_prompt(book_content, book_title)

        print(f"    Analyzing '{book_title}' to extract learning topics...")

        # Lower temperature on retries for more consistent output
        temperature = 0.3 - (retry_count * 0.1)  # 0.3, 0.2, 0.1

        response = self.llm_client.simple_prompt(
            prompt,
            system_message=None,  # Don't use system messages - not all models support them
            temperature=max(0.1, temperature),  # Don't go below 0.1
            max_tokens=4000,
        )

        # Try to parse JSON response with retry logic
        try:
            topics = self._parse_topics_response(response)
            print(f"    Extracted {len(topics)} topics")
            return topics
        except Exception as e:
            if retry_count < 2:  # Retry up to 2 times
                print(
                    f"    Parse failed (attempt {retry_count + 1}/3), retrying with stricter settings..."
                )
                return self._extract_topics_single(
                    book_content, book_title, retry_count + 1
                )
            else:
                # On final failure, try to extract manually from the response
                print(f"    All retries failed, attempting manual extraction...")
                topics = self._manual_topic_extraction(response)
                if topics:
                    print(f"    Manually extracted {len(topics)} topics")
                    return topics
                else:
                    print(f"    ERROR: Could not extract topics from response")
                    raise e

    def _extract_topics_from_chunks(
        self, book_content: str, book_title: str, max_chunk_words: int
    ) -> List[Dict]:
        """
        Extract topics from a large book by processing chunks with overlap and merging.

        Strategy:
        1. Split book into chunks with overlap (better context preservation)
        2. Extract topics from each chunk
        3. Merge and deduplicate topics
        4. Ask LLM to create final unified learning plan
        """
        # Use improved chunking with 10% overlap (200 words for 2000 word chunks)
        overlap_words = int(max_chunk_words * 0.1)
        chunks = self.chunk_text(book_content, max_chunk_words, overlap_words)

        print(f"Processing {len(chunks)} chunks with {overlap_words}-word overlap...")

        all_chunk_topics = []
        failed_chunks = []

        for i, chunk in enumerate(chunks, 1):
            print(f"Processing chunk {i}/{len(chunks)}...")

            try:
                chunk_topics = self._extract_topics_single(
                    chunk, f"{book_title} (Part {i})"
                )
                all_chunk_topics.extend(chunk_topics)
            except Exception as e:
                print(f"  ⚠️  ERROR processing chunk {i}/{len(chunks)}: {e}")
                print(f"  → Continuing with remaining chunks...")
                failed_chunks.append(i)
                continue

        # Report failures
        if failed_chunks:
            print(f"\nWarning: {len(failed_chunks)}/{len(chunks)} chunks failed to process")
            print(f"  Failed chunks: {', '.join(map(str, failed_chunks))}")
            print(f"  Successfully processed: {len(chunks) - len(failed_chunks)}/{len(chunks)} chunks")
        else:
            print(f"\nAll {len(chunks)} chunks processed successfully!")

        # Check if we got any topics at all
        if not all_chunk_topics:
            raise Exception(f"Failed to extract topics from any chunks. All {len(chunks)} chunks failed.")

        # Merge and refine topics
        print("Merging topics from all chunks...")
        final_topics = self._merge_topics(all_chunk_topics, book_title)

        return final_topics

    def _merge_topics(self, topics: List[Dict], book_title: str) -> List[Dict]:
        """
        Merge overlapping topics from multiple chunks.

        Args:
            topics: All topics from chunks
            book_title: Book title

        Returns:
            Merged and refined topic list
        """
        # Create a summary of all topics for LLM to merge
        topics_summary = "\n".join(
            [f"{i + 1}. {t['title']}: {t['description']}" for i, t in enumerate(topics)]
        )

        merge_prompt = f"""You are analyzing the book "{book_title}".

Below are learning topics extracted from different sections of the book. Some may overlap or be duplicates.

Topics:
{topics_summary}

Create a unified, comprehensive learning plan with 8-15 key topics that:
1. Merges overlapping/duplicate topics
2. Maintains logical progression
3. Covers all important concepts
4. Removes redundancy

Format as JSON:
[
  {{
    "topic_number": 1,
    "title": "Topic Title",
    "description": "What this topic covers",
    "importance": "High"
  }},
  ...
]

Respond ONLY with the JSON array."""

        response = self.llm_client.simple_prompt(
            merge_prompt, temperature=0.5, max_tokens=4000
        )

        merged_topics = self._parse_topics_response(response)

        print(f"Merged into {len(merged_topics)} final topics")

        return merged_topics

    @staticmethod
    def _manual_topic_extraction(response: str) -> List[Dict]:
        """
        Manually extract topics from malformed response.
        Fallback when JSON parsing fails.
        """
        topics = []

        # Look for individual topic objects in the text
        # Pattern: find all {...} objects that look like topics
        import re

        object_pattern = r'\{\s*"topic_number":\s*\d+[^}]*\}'
        matches = re.findall(object_pattern, response, re.DOTALL)

        for match in matches:
            try:
                # Clean up the object
                match = re.sub(r",\s*([}\]])", r"\1", match)  # Remove trailing commas
                match = re.sub(
                    r'"\s+"([a-z_]+)":', r'", "\1":', match
                )  # Fix missing commas

                topic = json.loads(match)

                # Ensure required fields
                if "title" in topic and "description" in topic:
                    if "topic_number" not in topic:
                        topic["topic_number"] = len(topics) + 1
                    if "importance" not in topic:
                        topic["importance"] = "Medium"
                    topics.append(topic)
            except:
                continue

        return topics if topics else None

    @staticmethod
    def _parse_topics_response(response: str) -> List[Dict]:
        """
        Parse LLM response containing topics JSON.

        Args:
            response: LLM response (should contain JSON array)

        Returns:
            List of topic dictionaries
        """
        # Try to extract JSON from response
        # Sometimes LLM adds extra text before/after JSON

        # Find JSON array in response - match the FIRST complete array
        # Look for [ followed by objects, stopping at the first ]
        json_match = re.search(
            r"\[\s*\{[^\]]*\}\s*(?:,\s*\{[^\]]*\}\s*)*\]", response, re.DOTALL
        )

        if json_match:
            json_str = json_match.group(0)
        else:
            # Fallback: try to find any array
            json_match = re.search(r"\[\s*\{.*?\}\s*\]", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Assume entire response is JSON
                json_str = response.strip()

        # Clean up common JSON formatting issues from LLM responses
        # Remove extra spaces in keys
        json_str = re.sub(r'"\s+([a-z_]+)\s*":', r'"\1":', json_str)
        # Fix capitalization issues in keys
        json_str = re.sub(
            r'"Topic\s+number":', r'"topic_number":', json_str, flags=re.IGNORECASE
        )
        json_str = re.sub(
            r'"Importance":', r'"importance":', json_str, flags=re.IGNORECASE
        )
        # Remove trailing commas before ] or }
        json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
        # Fix spaces in values
        json_str = re.sub(r':\s*"\s+', r': "', json_str)
        # Add missing commas between objects (} {  ->  }, {)
        json_str = re.sub(r"\}\s+\{", r"}, {", json_str)
        # Add missing commas after closing quotes before new keys (e.g., " "importance")
        json_str = re.sub(r'"\s+"([a-z_]+)":', r'", "\1":', json_str)

        try:
            topics = json.loads(json_str)

            # Validate structure
            if not isinstance(topics, list):
                raise ValueError("Response is not a list")

            for topic in topics:
                required_keys = ["title", "description"]
                if not all(key in topic for key in required_keys):
                    raise ValueError(f"Topic missing required keys: {topic}")

            # Ensure topic_number is set
            for i, topic in enumerate(topics, 1):
                if "topic_number" not in topic:
                    topic["topic_number"] = i

            return topics

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse topics JSON: {e}\nResponse: {response}")

    def process_book(self, book_path: str, output_dir: str = None) -> Dict:
        """
        Process a book: parse, extract topics, save results.

        Args:
            book_path: Path to book file (PDF/EPUB)
            output_dir: Directory to save processed data (defaults to config.PROCESSED_FOLDER)

        Returns:
            Dictionary with:
            - book_info: Book metadata
            - topics: Extracted topics
            - content: Full book text
        """
        import config

        output_dir = Path(output_dir or config.PROCESSED_FOLDER)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Parse book
        print(f"Parsing book: {book_path}")
        book_data = DocumentParser.parse(book_path)

        # Extract topics (using chapters if available)
        chapters = book_data.get("chapters", [])
        if chapters:
            print(f"Found {len(chapters)} chapters in the book")

        topics = self.extract_topics(
            book_data["content"], book_data["title"], chapters=chapters
        )

        # Create output structure
        result = {
            "book_info": {
                "title": book_data["title"],
                "file_name": Path(book_path).name,
                "metadata": book_data.get("metadata", {}),
                "word_count": len(book_data["content"].split()),
                "page_count": book_data.get("page_count", 0),
            },
            "topics": topics,
            "content": book_data["content"],
        }

        # Save to file
        safe_filename = (
            re.sub(r"[^\w\s-]", "", book_data["title"]).strip().replace(" ", "_")
        )
        output_file = output_dir / f"{safe_filename}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"Saved processed book to: {output_file}")

        return result


if __name__ == "__main__":
    # Simple test
    import sys

    if len(sys.argv) > 1:
        book_path = sys.argv[1]

        extractor = TopicExtractor()
        result = extractor.process_book(book_path)

        print(f"\n{'=' * 60}")
        print(f"Book: {result['book_info']['title']}")
        print(f"Word count: {result['book_info']['word_count']}")
        print(f"\nLearning Plan ({len(result['topics'])} topics):")
        print(f"{'=' * 60}\n")

        for topic in result["topics"]:
            importance = topic.get("importance", "Medium")
            print(f"{topic['topic_number']}. [{importance}] {topic['title']}")
            print(f"   {topic['description']}\n")
    else:
        print("Usage: python topic_extractor.py <path_to_book>")
