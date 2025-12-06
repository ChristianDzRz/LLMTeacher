"""
Context manager for extracting and managing relevant content for each topic.
"""

import re
from typing import Dict, List, Tuple

from src.llm_client import LLMClient
from src.text_splitter import ImprovedTextSplitter


class ContextManager:
    """Extract and manage relevant book content for specific topics."""

    def __init__(self, llm_client: LLMClient = None):
        """
        Initialize context manager.

        Args:
            llm_client: LLM client instance (creates new one if not provided)
        """
        self.llm_client = llm_client or LLMClient()

    @staticmethod
    def split_into_passages(
        text: str, passage_size: int = 500, overlap_ratio: float = 0.2
    ) -> List[Tuple[str, int]]:
        """
        Split text into passages with overlap for better context preservation.

        Uses improved text splitting with configurable overlap based on best practices:
        - 20% overlap (default) maintains context across passages
        - Respects paragraph boundaries
        - Character-based sizing for precision

        Args:
            text: Full text content
            passage_size: Target characters per passage (default 500)
            overlap_ratio: Fraction of passage_size to overlap (default 0.2 = 20%)

        Returns:
            List of (passage_text, start_position) tuples
        """
        # Calculate overlap size (20% of passage size is recommended)
        overlap_size = int(passage_size * overlap_ratio)

        # Use improved text splitter with overlap
        splitter = ImprovedTextSplitter(
            chunk_size=passage_size,
            chunk_overlap=overlap_size,
            separator="\n\n",
        )

        return splitter.split_text_with_positions(text)

    def extract_relevant_context(
        self,
        topic: Dict,
        book_content: str,
        max_context_words: int = 3000,
        use_llm: bool = True,
    ) -> Dict:
        """
        Extract relevant content from book for a specific topic.

        Args:
            topic: Topic dictionary with 'title' and 'description'
            book_content: Full book text
            max_context_words: Maximum words in context
            use_llm: Whether to use LLM for relevance ranking (more accurate but slower)

        Returns:
            Dictionary with:
            - context: Relevant text passages
            - passages: List of individual passages
            - word_count: Total words in context
        """
        if use_llm:
            return self._extract_context_with_llm(
                topic, book_content, max_context_words
            )
        else:
            return self._extract_context_keyword(topic, book_content, max_context_words)

    def _extract_context_keyword(
        self, topic: Dict, book_content: str, max_context_words: int
    ) -> Dict:
        """
        Extract context using keyword matching (fast, less accurate).

        Simple approach: find passages containing topic keywords.
        """
        topic_title = topic["title"]
        topic_desc = topic["description"]

        # Extract keywords from topic
        keywords = self._extract_keywords(f"{topic_title} {topic_desc}")

        # Split book into passages with overlap for better context
        passages = self.split_into_passages(
            book_content, passage_size=1000, overlap_ratio=0.2
        )

        # Score each passage based on keyword matches
        scored_passages = []

        for passage_text, start_pos in passages:
            passage_lower = passage_text.lower()
            score = 0

            for keyword in keywords:
                keyword_lower = keyword.lower()
                # Count occurrences
                count = passage_lower.count(keyword_lower)
                score += count

            if score > 0:
                scored_passages.append((score, passage_text, start_pos))

        # Sort by score (highest first)
        scored_passages.sort(reverse=True, key=lambda x: x[0])

        # Collect top passages until we reach max_context_words
        selected_passages = []
        total_words = 0

        for score, passage, start_pos in scored_passages:
            passage_words = len(passage.split())

            if total_words + passage_words <= max_context_words:
                selected_passages.append(passage)
                total_words += passage_words

            if total_words >= max_context_words * 0.9:  # 90% threshold
                break

        # Join passages
        context = "\n\n---\n\n".join(selected_passages)

        return {
            "context": context,
            "passages": selected_passages,
            "word_count": total_words,
            "method": "keyword",
        }

    def _extract_context_with_llm(
        self, topic: Dict, book_content: str, max_context_words: int
    ) -> Dict:
        """
        Extract context using LLM for relevance ranking (slower, more accurate).

        Strategy:
        1. Split book into passages with overlap
        2. Ask LLM to identify most relevant passages for topic
        3. Return top passages
        """
        topic_title = topic["title"]
        topic_desc = topic["description"]

        # Split book into passages with overlap for better context
        passages = self.split_into_passages(
            book_content, passage_size=1000, overlap_ratio=0.2
        )

        # For very large books, use keyword pre-filtering
        if len(passages) > 50:
            print(f"Pre-filtering {len(passages)} passages using keywords...")
            keyword_result = self._extract_context_keyword(
                topic, book_content, max_context_words * 3
            )
            # Now work with this subset
            passages = [(p, i) for i, p in enumerate(keyword_result["passages"])]

        # Prepare passages for LLM evaluation
        passages_text = "\n\n".join(
            [
                f"[Passage {i + 1}]\n{passage}"
                for i, (passage, _) in enumerate(passages[:50])  # Limit to 50 passages
            ]
        )

        relevance_prompt = f"""Topic: {topic_title}
Description: {topic_desc}

Below are passages from a book. Identify the passage numbers that are MOST RELEVANT to this topic.

{passages_text}

Return ONLY a JSON array of the most relevant passage numbers (top 5-10), ordered by relevance:
[1, 5, 12, ...]

Consider a passage relevant if it:
- Directly discusses the topic
- Provides essential background or context
- Contains key examples or explanations
- Is necessary for understanding the topic

Respond ONLY with the JSON array of passage numbers."""

        print(
            f"Analyzing {len(passages[:50])} passages for relevance to '{topic_title}'..."
        )

        response = self.llm_client.simple_prompt(
            relevance_prompt, temperature=0.3, max_tokens=500
        )

        # Parse relevant passage numbers
        relevant_indices = self._parse_passage_numbers(response)

        # Collect relevant passages
        selected_passages = []
        total_words = 0

        for idx in relevant_indices:
            if idx < 1 or idx > len(passages):
                continue

            passage_text = passages[idx - 1][0]  # -1 because LLM uses 1-based indexing
            passage_words = len(passage_text.split())

            if total_words + passage_words <= max_context_words:
                selected_passages.append(passage_text)
                total_words += passage_words

            if total_words >= max_context_words * 0.9:
                break

        # If we didn't get enough content, add a few more passages
        if total_words < max_context_words * 0.5 and len(selected_passages) < 3:
            print("Warning: Limited relevant content found, using keyword fallback...")
            return self._extract_context_keyword(topic, book_content, max_context_words)

        context = "\n\n---\n\n".join(selected_passages)

        return {
            "context": context,
            "passages": selected_passages,
            "word_count": total_words,
            "method": "llm",
        }

    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        """Extract important keywords from text."""
        # Remove common stop words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "was",
            "are",
            "were",
            "been",
            "be",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "should",
            "could",
            "may",
            "might",
            "must",
            "can",
            "this",
            "that",
            "these",
            "those",
            "what",
            "which",
            "who",
            "when",
            "where",
            "why",
            "how",
        }

        # Extract words
        words = re.findall(r"\b[a-z]+\b", text.lower())

        # Filter out stop words and short words
        keywords = [w for w in words if w not in stop_words and len(w) > 3]

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)

        return unique_keywords

    @staticmethod
    def _parse_passage_numbers(response: str) -> List[int]:
        """Parse passage numbers from LLM response."""
        # Try to extract JSON array
        json_match = re.search(r"\[[\d,\s]+\]", response)

        if json_match:
            json_str = json_match.group(0)
            import json

            try:
                numbers = json.loads(json_str)
                return [int(n) for n in numbers if isinstance(n, (int, float))]
            except:
                pass

        # Fallback: extract all numbers from response
        numbers = re.findall(r"\b\d+\b", response)
        return [int(n) for n in numbers[:15]]  # Limit to top 15

    def build_topic_contexts(
        self, topics: List[Dict], book_content: str, use_llm: bool = True
    ) -> Dict[int, Dict]:
        """
        Build context for all topics.

        Args:
            topics: List of topic dictionaries
            book_content: Full book text
            use_llm: Whether to use LLM for context extraction

        Returns:
            Dictionary mapping topic_number to context data
        """
        topic_contexts = {}

        for i, topic in enumerate(topics, 1):
            print(f"\nExtracting context for topic {i}/{len(topics)}: {topic['title']}")

            context_data = self.extract_relevant_context(
                topic, book_content, max_context_words=3000, use_llm=use_llm
            )

            topic_contexts[topic["topic_number"]] = context_data

            print(
                f"  → Extracted {context_data['word_count']} words using {context_data['method']} method"
            )

        return topic_contexts


if __name__ == "__main__":
    # Simple test
    import json
    import sys

    if len(sys.argv) > 1:
        # Load processed book data
        processed_file = sys.argv[1]

        with open(processed_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        manager = ContextManager()

        # Build contexts for all topics
        use_llm = len(sys.argv) > 2 and sys.argv[2] == "--llm"

        contexts = manager.build_topic_contexts(
            data["topics"], data["content"], use_llm=use_llm
        )

        # Save contexts
        output_file = processed_file.replace(".json", "_contexts.json")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(contexts, f, indent=2, ensure_ascii=False)

        print(f"\nSaved topic contexts to: {output_file}")
    else:
        print("Usage: python context_manager.py <processed_book.json> [--llm]")
        print("  --llm: Use LLM for context extraction (slower but more accurate)")
