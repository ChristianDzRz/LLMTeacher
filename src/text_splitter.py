"""
Improved text splitting with overlap for better context preservation.

Based on best practices from:
- LangChain's CharacterTextSplitter
- DocMind AI's chunking strategies
- GeeksforGeeks LLM PDF summarizer patterns
"""

import re
from typing import List, Tuple


class ImprovedTextSplitter:
    """
    Advanced text splitter with overlap for context preservation.

    Implements best practices:
    - Configurable chunk size and overlap
    - Separator-based splitting (respects paragraphs)
    - Overlap maintains context across chunk boundaries
    - Character-based sizing (more precise than word-based)
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separator: str = "\n\n",
        length_function=len,
    ):
        """
        Initialize text splitter.

        Args:
            chunk_size: Maximum characters per chunk (default 1000)
            chunk_overlap: Characters to overlap between chunks (default 200, 20%)
            separator: Primary separator for splitting (default paragraph separator)
            length_function: Function to measure text length (default: character count)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator
        self.length_function = length_function

        # Validate overlap
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

    def split_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Full text to split

        Returns:
            List of text chunks with overlap
        """
        # Split by separator first (preserve paragraph boundaries)
        splits = text.split(self.separator)

        # Filter out empty splits
        splits = [s for s in splits if s.strip()]

        # Merge splits into chunks with overlap
        chunks = self._merge_splits(splits)

        return chunks

    def split_text_with_positions(self, text: str) -> List[Tuple[str, int]]:
        """
        Split text into chunks and track their positions in original text.

        Args:
            text: Full text to split

        Returns:
            List of (chunk_text, start_position) tuples
        """
        # Split by separator
        splits = text.split(self.separator)
        splits = [s for s in splits if s.strip()]

        # Track positions
        position = 0
        split_positions = []

        for split in splits:
            split_positions.append((split, position))
            # Account for separator length
            position += len(split) + len(self.separator)

        # Merge splits into chunks while tracking positions
        chunks_with_positions = self._merge_splits_with_positions(split_positions)

        return chunks_with_positions

    def _merge_splits(self, splits: List[str]) -> List[str]:
        """
        Merge splits into chunks respecting chunk_size and chunk_overlap.

        Args:
            splits: List of text segments (e.g., paragraphs)

        Returns:
            List of merged chunks
        """
        chunks = []
        current_chunk = []
        current_length = 0

        for split in splits:
            split_length = self.length_function(split)

            # If single split exceeds chunk_size, add it as its own chunk
            if split_length > self.chunk_size:
                # Save current chunk if it exists
                if current_chunk:
                    chunks.append(self.separator.join(current_chunk))
                    current_chunk = []
                    current_length = 0

                # Add large split as standalone chunk
                chunks.append(split)
                continue

            # Check if adding this split would exceed chunk_size
            # Account for separator length
            separator_length = len(self.separator) if current_chunk else 0

            if current_length + separator_length + split_length > self.chunk_size:
                # Save current chunk
                if current_chunk:
                    chunks.append(self.separator.join(current_chunk))

                # Calculate overlap: take last N characters from previous chunk
                overlap_text = self._get_overlap_text(current_chunk)

                # Start new chunk with overlap
                current_chunk = [overlap_text, split] if overlap_text else [split]
                current_length = sum(self.length_function(s) for s in current_chunk)
            else:
                # Add to current chunk
                current_chunk.append(split)
                current_length += split_length + separator_length

        # Add remaining chunk
        if current_chunk:
            chunks.append(self.separator.join(current_chunk))

        return chunks

    def _merge_splits_with_positions(
        self, split_positions: List[Tuple[str, int]]
    ) -> List[Tuple[str, int]]:
        """
        Merge splits into chunks while tracking start positions.

        Args:
            split_positions: List of (split_text, position) tuples

        Returns:
            List of (chunk_text, start_position) tuples
        """
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_start_pos = 0

        for i, (split, pos) in enumerate(split_positions):
            split_length = self.length_function(split)

            # Track chunk start position
            if not current_chunk:
                chunk_start_pos = pos

            # If single split exceeds chunk_size, add it as its own chunk
            if split_length > self.chunk_size:
                if current_chunk:
                    chunks.append((self.separator.join(current_chunk), chunk_start_pos))
                    current_chunk = []
                    current_length = 0

                chunks.append((split, pos))
                continue

            # Check if adding this split would exceed chunk_size
            separator_length = len(self.separator) if current_chunk else 0

            if current_length + separator_length + split_length > self.chunk_size:
                # Save current chunk
                if current_chunk:
                    chunks.append((self.separator.join(current_chunk), chunk_start_pos))

                # Calculate overlap
                overlap_text = self._get_overlap_text(current_chunk)

                # Start new chunk with overlap
                # Position should still be from the non-overlap part
                if overlap_text:
                    current_chunk = [overlap_text, split]
                    # Estimate overlap start position (approximate)
                    overlap_length = self.length_function(overlap_text)
                    chunk_start_pos = pos - overlap_length - len(self.separator)
                else:
                    current_chunk = [split]
                    chunk_start_pos = pos

                current_length = sum(self.length_function(s) for s in current_chunk)
            else:
                current_chunk.append(split)
                current_length += split_length + separator_length

        # Add remaining chunk
        if current_chunk:
            chunks.append((self.separator.join(current_chunk), chunk_start_pos))

        return chunks

    def _get_overlap_text(self, chunks: List[str]) -> str:
        """
        Extract overlap text from end of current chunks.

        Args:
            chunks: List of text segments in current chunk

        Returns:
            Text to use as overlap in next chunk
        """
        if not chunks or self.chunk_overlap == 0:
            return ""

        # Get last N characters from joined chunks
        full_text = self.separator.join(chunks)

        if len(full_text) <= self.chunk_overlap:
            return full_text

        # Get last chunk_overlap characters
        overlap = full_text[-self.chunk_overlap :]

        # Try to start at a word boundary for cleaner overlap
        # Find first space in overlap
        space_idx = overlap.find(" ")
        if space_idx > 0 and space_idx < len(overlap) // 2:
            overlap = overlap[space_idx + 1 :]

        return overlap


class SemanticTextSplitter(ImprovedTextSplitter):
    """
    Semantic text splitter that respects sentence boundaries.

    Better for creating chunks that maintain semantic coherence.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        length_function=len,
    ):
        """
        Initialize semantic text splitter.

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Characters to overlap between chunks
            length_function: Function to measure text length
        """
        # Use period + space as separator (sentence boundary)
        # But we'll implement custom splitting logic
        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator="\n\n",  # Still prefer paragraph boundaries
            length_function=length_function,
        )

    def split_text(self, text: str) -> List[str]:
        """
        Split text at semantic boundaries (paragraphs > sentences > words).

        Args:
            text: Full text to split

        Returns:
            List of semantically coherent chunks
        """
        # First try paragraph splitting
        paragraphs = text.split("\n\n")
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        # For very large paragraphs, split by sentences
        splits = []
        for para in paragraphs:
            if len(para) > self.chunk_size * 1.5:
                # Split large paragraph into sentences
                sentences = self._split_sentences(para)
                splits.extend(sentences)
            else:
                splits.append(para)

        # Merge splits into chunks
        chunks = self._merge_splits(splits)

        return chunks

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """
        Split text into sentences.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Simple sentence splitting (can be improved with NLTK if needed)
        # Split on period, exclamation, question mark followed by space or newline
        sentence_endings = r"([.!?])\s+"

        sentences = re.split(sentence_endings, text)

        # Recombine sentences with their punctuation
        result = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                sentence = sentences[i] + sentences[i + 1]
                result.append(sentence.strip())

        # Add last sentence if it doesn't have punctuation
        if len(sentences) % 2 == 1:
            result.append(sentences[-1].strip())

        return [s for s in result if s]


# Utility functions for backward compatibility
def split_into_passages(
    text: str, passage_size: int = 500, overlap: int = 100
) -> List[Tuple[str, int]]:
    """
    Split text into passages with overlap (backward compatible interface).

    Args:
        text: Full text content
        passage_size: Target characters per passage (default 500)
        overlap: Characters to overlap (default 100, 20%)

    Returns:
        List of (passage_text, start_position) tuples
    """
    # Convert word-based size to character-based (approximate)
    # Assume average word length of 5 characters + 1 space
    char_size = passage_size * 6
    char_overlap = overlap * 6

    splitter = ImprovedTextSplitter(
        chunk_size=char_size,
        chunk_overlap=char_overlap,
        separator="\n\n",
    )

    return splitter.split_text_with_positions(text)


def chunk_text(text: str, max_words: int = 2000, overlap_words: int = 200) -> List[str]:
    """
    Chunk text with overlap (backward compatible interface).

    Args:
        text: Full text content
        max_words: Maximum words per chunk
        overlap_words: Words to overlap between chunks

    Returns:
        List of text chunks
    """
    # Convert to character-based
    char_size = max_words * 6
    char_overlap = overlap_words * 6

    splitter = ImprovedTextSplitter(
        chunk_size=char_size,
        chunk_overlap=char_overlap,
        separator="\n\n",
    )

    return splitter.split_text(text)


if __name__ == "__main__":
    # Test the text splitter
    sample_text = """
    This is the first paragraph. It contains multiple sentences. This helps demonstrate the chunking behavior.

    This is the second paragraph. It also has several sentences to show how the text splitter works.

    Here's a third paragraph with important information that should be maintained.

    The fourth paragraph discusses additional concepts and ideas that are relevant to the topic.

    Finally, we have a fifth paragraph to ensure we have enough content for testing the overlap functionality.
    """

    print("Testing ImprovedTextSplitter:")
    print("=" * 60)

    splitter = ImprovedTextSplitter(chunk_size=150, chunk_overlap=30)
    chunks = splitter.split_text(sample_text)

    for i, chunk in enumerate(chunks, 1):
        print(f"\nChunk {i} ({len(chunk)} chars):")
        print(chunk[:100] + "..." if len(chunk) > 100 else chunk)

    print("\n\nTesting with positions:")
    print("=" * 60)

    chunks_with_pos = splitter.split_text_with_positions(sample_text)

    for i, (chunk, pos) in enumerate(chunks_with_pos, 1):
        print(f"\nChunk {i} (position {pos}, {len(chunk)} chars):")
        print(chunk[:100] + "..." if len(chunk) > 100 else chunk)
