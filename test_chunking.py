"""
Test script to demonstrate improved chunking on a real book.

This script will:
1. Process a book with the improved chunking
2. Show statistics about chunks and overlap
3. Demonstrate context preservation
"""

import json
from pathlib import Path

from src.context_manager import ContextManager
from src.text_splitter import ImprovedTextSplitter
from src.topic_extractor import TopicExtractor


def analyze_chunking(book_path: str):
    """Analyze chunking behavior on a real book."""

    print("\n" + "=" * 80)
    print("TESTING IMPROVED CHUNKING WITH OVERLAP")
    print("=" * 80)

    print(f"\n📚 Book: {Path(book_path).name}")

    # Initialize components
    extractor = TopicExtractor()

    # Parse the book (without extracting topics yet)
    from src.document_parser import DocumentParser

    print("\n⏳ Parsing book...")
    book_data = DocumentParser.parse(book_path)

    print(f"✅ Book parsed successfully!")
    print(f"   Title: {book_data['title']}")
    print(f"   Pages: {book_data.get('page_count', 'N/A')}")
    print(f"   Words: {len(book_data['content'].split()):,}")
    print(f"   Characters: {len(book_data['content']):,}")

    # Test different chunking strategies
    print("\n" + "-" * 80)
    print("CHUNKING COMPARISON")
    print("-" * 80)

    content = book_data["content"]

    # 1. Old style (no overlap - simulated)
    print("\n❌ OLD METHOD (No Overlap):")
    old_splitter = ImprovedTextSplitter(
        chunk_size=12000,  # ~2000 words
        chunk_overlap=0,  # NO OVERLAP
        separator="\n\n",
    )
    old_chunks = old_splitter.split_text(content)
    print(f"   Chunks created: {len(old_chunks)}")
    print(
        f"   Avg chunk size: {sum(len(c) for c in old_chunks) / len(old_chunks):.0f} chars"
    )
    print(f"   Total chars (with overlap): {sum(len(c) for c in old_chunks):,}")

    # 2. New style (10% overlap)
    print("\n✅ NEW METHOD (10% Overlap):")
    new_splitter = ImprovedTextSplitter(
        chunk_size=12000,  # ~2000 words
        chunk_overlap=1200,  # 10% overlap
        separator="\n\n",
    )
    new_chunks = new_splitter.split_text(content)
    print(f"   Chunks created: {len(new_chunks)}")
    print(
        f"   Avg chunk size: {sum(len(c) for c in new_chunks) / len(new_chunks):.0f} chars"
    )
    print(f"   Total chars (with overlap): {sum(len(c) for c in new_chunks):,}")
    print(
        f"   Overhead from overlap: {(sum(len(c) for c in new_chunks) / len(content) - 1) * 100:.1f}%"
    )

    # 3. Context extraction chunks (20% overlap)
    print("\n✅ CONTEXT EXTRACTION (20% Overlap):")
    context_splitter = ImprovedTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,  # 20% overlap
        separator="\n\n",
    )
    context_chunks = context_splitter.split_text(content)
    print(f"   Chunks created: {len(context_chunks)}")
    print(
        f"   Avg chunk size: {sum(len(c) for c in context_chunks) / len(context_chunks):.0f} chars"
    )
    print(f"   Total chars (with overlap): {sum(len(c) for c in context_chunks):,}")
    print(
        f"   Overhead from overlap: {(sum(len(c) for c in context_chunks) / len(content) - 1) * 100:.1f}%"
    )

    # Demonstrate overlap preservation
    print("\n" + "-" * 80)
    print("OVERLAP DEMONSTRATION")
    print("-" * 80)

    if len(new_chunks) >= 2:
        chunk1_end = new_chunks[0][-300:]
        chunk2_start = new_chunks[1][:300:]

        print("\n📄 Chunk 1 ending:")
        print("   ..." + chunk1_end)

        print("\n📄 Chunk 2 beginning:")
        print("   " + chunk2_start + "...")

        # Find overlap
        overlap_detected = False
        for i in range(100, min(len(chunk1_end), len(chunk2_start))):
            if chunk1_end[-i:] == chunk2_start[:i]:
                print(f"\n✅ Overlap detected: {i} characters")
                print(f"   Overlapping text: '{chunk1_end[-i:][:100]}...'")
                overlap_detected = True
                break

        if not overlap_detected:
            # Check if there's partial overlap
            for i in range(50, 200):
                snippet = chunk1_end[-i:]
                if snippet in chunk2_start:
                    print(f"\n✅ Partial overlap found: ~{i} characters")
                    print(f"   Overlapping text: '{snippet[:100]}...'")
                    break

    # Show chunk boundaries
    print("\n" + "-" * 80)
    print("CHUNK BOUNDARIES (First 3 chunks)")
    print("-" * 80)

    for i, chunk in enumerate(new_chunks[:3], 1):
        words = chunk.split()
        print(f"\n📑 Chunk {i}:")
        print(f"   Size: {len(chunk)} chars, {len(words)} words")
        print(f"   Starts: {' '.join(words[:15])}...")
        print(f"   Ends: ...{' '.join(words[-15:])}")

    return {
        "old_chunks": len(old_chunks),
        "new_chunks": len(new_chunks),
        "context_chunks": len(context_chunks),
        "book_data": book_data,
    }


def test_topic_extraction(book_path: str, test_data: dict):
    """Test topic extraction with improved chunking."""

    print("\n" + "=" * 80)
    print("TESTING TOPIC EXTRACTION WITH IMPROVED CHUNKING")
    print("=" * 80)

    print("\n⏳ Extracting topics with improved chunking...")
    print("   (This will use 10% overlap between chunks)")

    extractor = TopicExtractor()

    try:
        # Extract topics using the improved chunking
        topics = extractor.extract_topics(
            test_data["book_data"]["content"],
            test_data["book_data"]["title"],
            chapters=test_data["book_data"].get("chapters", []),
        )

        print(f"\n✅ Topics extracted: {len(topics)}")
        print("\n" + "-" * 80)
        print("EXTRACTED TOPICS")
        print("-" * 80)

        for topic in topics[:5]:  # Show first 5
            print(f"\n{topic['topic_number']}. {topic['title']}")
            print(f"   Importance: {topic.get('importance', 'N/A')}")
            print(f"   Description: {topic['description'][:150]}...")

        if len(topics) > 5:
            print(f"\n... and {len(topics) - 5} more topics")

        return topics

    except Exception as e:
        print(f"\n❌ Error during topic extraction: {e}")
        import traceback

        traceback.print_exc()
        return None


def test_context_extraction(book_data: dict, topics: list):
    """Test context extraction with improved chunking."""

    if not topics:
        print("\n⚠️ No topics available for context extraction test")
        return

    print("\n" + "=" * 80)
    print("TESTING CONTEXT EXTRACTION WITH IMPROVED CHUNKING")
    print("=" * 80)

    print("\n⏳ Extracting context for first topic...")
    print("   (This will use 20% overlap between passages)")

    manager = ContextManager()

    # Test with first topic
    topic = topics[0]
    print(f"\n📌 Topic: {topic['title']}")

    try:
        context_data = manager.extract_relevant_context(
            topic,
            book_data["content"],
            max_context_words=3000,
            use_llm=False,  # Use keyword method for speed
        )

        print(f"\n✅ Context extracted:")
        print(f"   Method: {context_data['method']}")
        print(f"   Passages found: {len(context_data['passages'])}")
        print(f"   Total words: {context_data['word_count']}")

        print("\n" + "-" * 80)
        print("SAMPLE PASSAGE")
        print("-" * 80)

        if context_data["passages"]:
            sample = context_data["passages"][0]
            print(f"\n{sample[:500]}...")
            print(f"\n... ({len(sample)} characters total)")

        return context_data

    except Exception as e:
        print(f"\n❌ Error during context extraction: {e}")
        import traceback

        traceback.print_exc()
        return None


def main():
    """Run all tests."""

    # Find a book to test
    book_path = Path(
        "data/books/Learning_SQL__Generate_Manipulate_and_Retrieve_Data_--_Alan_Beaulieu_--_2020_--_OReilly_Media_Incorporated_--_9781492057611_--_089bb3c2d0f555be4c292251f45c4863_--_Annas_Archive.pdf"
    )

    if not book_path.exists():
        print(f"❌ Book not found: {book_path}")
        print("\nAvailable books:")
        books_dir = Path("data/books")
        if books_dir.exists():
            for book in books_dir.glob("*.pdf"):
                print(f"  - {book.name}")
            for book in books_dir.glob("*.epub"):
                print(f"  - {book.name}")
        return

    # Test 1: Analyze chunking
    test_data = analyze_chunking(str(book_path))

    # Test 2: Topic extraction
    topics = test_topic_extraction(str(book_path), test_data)

    # Test 3: Context extraction
    if topics:
        context_data = test_context_extraction(test_data["book_data"], topics)

    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 80)
    print("\nKey Findings:")
    print(f"  • Old chunking (no overlap): {test_data['old_chunks']} chunks")
    print(f"  • New chunking (10% overlap): {test_data['new_chunks']} chunks")
    print(f"  • Context chunks (20% overlap): {test_data['context_chunks']} passages")
    print(f"  • Topics extracted: {len(topics) if topics else 0}")
    print("\n💡 The improved chunking preserves context across chunk boundaries!")
    print("   This leads to better topic extraction and context retrieval.\n")


if __name__ == "__main__":
    main()
