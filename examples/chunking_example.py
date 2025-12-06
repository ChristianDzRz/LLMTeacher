"""
Example demonstrating improved text chunking with overlap.

This example shows how the improved chunking strategy preserves context
across chunk boundaries using overlap.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.text_splitter import ImprovedTextSplitter, SemanticTextSplitter


def visualize_chunks(text: str, chunk_size: int, chunk_overlap: int):
    """Visualize how text is split into chunks with overlap."""

    print(f"\n{'=' * 70}")
    print(
        f"Chunking Demo: {chunk_size} chars, {chunk_overlap} char overlap ({chunk_overlap / chunk_size * 100:.0f}%)"
    )
    print(f"{'=' * 70}\n")

    splitter = ImprovedTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, separator="\n\n"
    )

    chunks = splitter.split_text_with_positions(text)

    print(f"Original text length: {len(text)} characters")
    print(f"Number of chunks: {len(chunks)}\n")

    for i, (chunk, pos) in enumerate(chunks, 1):
        print(f"\n{'─' * 70}")
        print(f"Chunk {i} (position {pos}, {len(chunk)} chars)")
        print(f"{'─' * 70}")

        # Show first and last 100 chars
        if len(chunk) > 200:
            preview = chunk[:100] + "\n...\n" + chunk[-100:]
        else:
            preview = chunk

        print(preview)

        # Highlight overlap with previous chunk
        if i > 1:
            prev_chunk = chunks[i - 2][0]
            # Find overlap
            overlap_start = max(0, len(prev_chunk) - chunk_overlap - 50)
            prev_end = prev_chunk[overlap_start:]

            # Check if there's actual overlap in content
            if chunk.startswith(prev_end[:50]) or prev_end[-50:] in chunk[:100]:
                print(f"\n📎 Overlap detected with Chunk {i - 1}")


def compare_with_without_overlap(text: str):
    """Compare chunking with and without overlap."""

    print(f"\n{'=' * 70}")
    print("Comparison: With vs Without Overlap")
    print(f"{'=' * 70}\n")

    chunk_size = 300

    # Without overlap
    print("❌ WITHOUT OVERLAP (old method)")
    print("─" * 70)
    splitter_no_overlap = ImprovedTextSplitter(
        chunk_size=chunk_size, chunk_overlap=0, separator="\n\n"
    )
    chunks_no_overlap = splitter_no_overlap.split_text(text)
    print(f"Number of chunks: {len(chunks_no_overlap)}")
    for i, chunk in enumerate(chunks_no_overlap[:2], 1):
        print(f"\nChunk {i} ends with: ...{chunk[-80:]}")

    print("\n")

    # With overlap
    print("✅ WITH OVERLAP (new method)")
    print("─" * 70)
    splitter_with_overlap = ImprovedTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=60,  # 20% overlap
        separator="\n\n",
    )
    chunks_with_overlap = splitter_with_overlap.split_text(text)
    print(f"Number of chunks: {len(chunks_with_overlap)}")
    for i, chunk in enumerate(chunks_with_overlap[:2], 1):
        if i == 1:
            print(f"\nChunk {i} ends with: ...{chunk[-80:]}")
        else:
            print(f"\nChunk {i} starts with: {chunk[:80]}...")
            print(f"         ends with: ...{chunk[-80:]}")

    print("\n💡 Notice how Chunk 2 includes context from Chunk 1's ending!")


def main():
    """Run chunking examples."""

    # Sample book-like text
    sample_text = """
    Machine learning is a subset of artificial intelligence that focuses on developing systems that can learn from data. These systems improve their performance over time without being explicitly programmed.

    The fundamental concept behind machine learning is pattern recognition. By analyzing large amounts of data, machine learning algorithms can identify patterns and make predictions or decisions based on those patterns.

    There are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning. Each approach has its own strengths and is suited to different types of problems.

    Supervised learning involves training a model on labeled data. The algorithm learns to map inputs to outputs based on example input-output pairs. Common applications include image classification and spam detection.

    Unsupervised learning works with unlabeled data. The algorithm tries to find hidden patterns or structures in the data without being told what to look for. Clustering and dimensionality reduction are typical unsupervised learning tasks.

    Reinforcement learning is about learning through interaction with an environment. An agent learns to make decisions by receiving rewards or penalties for its actions. This approach is widely used in robotics and game playing.

    Neural networks are a key technology in modern machine learning. Inspired by the human brain, these networks consist of interconnected nodes that process information in layers.

    Deep learning is a specialized form of machine learning that uses neural networks with many layers. These deep neural networks have achieved remarkable results in areas like computer vision and natural language processing.
    """

    print("\n" + "=" * 70)
    print("IMPROVED TEXT CHUNKING DEMONSTRATION")
    print("=" * 70)

    # Example 1: Standard chunking
    print("\n\n📚 EXAMPLE 1: Standard Chunking (1000 chars, 20% overlap)")
    visualize_chunks(sample_text, chunk_size=1000, chunk_overlap=200)

    # Example 2: Smaller chunks
    print("\n\n📚 EXAMPLE 2: Smaller Chunks (500 chars, 20% overlap)")
    visualize_chunks(sample_text, chunk_size=500, chunk_overlap=100)

    # Example 3: Comparison
    print("\n\n📚 EXAMPLE 3: Comparison")
    compare_with_without_overlap(sample_text)

    # Example 4: Semantic splitter
    print("\n\n📚 EXAMPLE 4: Semantic Text Splitter")
    print("=" * 70)
    semantic_splitter = SemanticTextSplitter(chunk_size=500, chunk_overlap=100)
    semantic_chunks = semantic_splitter.split_text(sample_text)
    print(f"Semantic chunks created: {len(semantic_chunks)}")
    print("\nFirst semantic chunk:")
    print("─" * 70)
    print(semantic_chunks[0] if semantic_chunks else "No chunks")

    # Show statistics
    print("\n\n📊 STATISTICS")
    print("=" * 70)
    print(f"Original text: {len(sample_text)} characters")
    print(f"Original text: {len(sample_text.split())} words")
    print(f"\nChunking configurations tested:")
    print(
        f"  • 1000 chars, 20% overlap: {len(ImprovedTextSplitter(1000, 200).split_text(sample_text))} chunks"
    )
    print(
        f"  • 500 chars, 20% overlap:  {len(ImprovedTextSplitter(500, 100).split_text(sample_text))} chunks"
    )
    print(
        f"  • 300 chars, 20% overlap:  {len(ImprovedTextSplitter(300, 60).split_text(sample_text))} chunks"
    )
    print(f"  • Semantic (500 chars):    {len(semantic_chunks)} chunks")

    print("\n✅ Chunking demonstration complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
