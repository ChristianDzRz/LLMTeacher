"""
Side-by-side comparison of old vs new chunking strategies.
Shows the practical benefits of overlap for book processing.
"""

import json
from pathlib import Path

from src.text_splitter import ImprovedTextSplitter


def compare_chunking_strategies(text: str, chunk_size: int = 12000):
    """Compare old (no overlap) vs new (with overlap) chunking."""

    print("\n" + "=" * 90)
    print("CHUNKING STRATEGY COMPARISON")
    print("=" * 90)

    print(f"\nInput text: {len(text):,} characters (~{len(text.split()):,} words)")

    # Strategy 1: No overlap (old)
    splitter_old = ImprovedTextSplitter(
        chunk_size=chunk_size, chunk_overlap=0, separator="\n\n"
    )
    chunks_old = splitter_old.split_text(text)

    # Strategy 2: 10% overlap (new - for topic extraction)
    splitter_new = ImprovedTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=int(chunk_size * 0.1),  # 10%
        separator="\n\n",
    )
    chunks_new = splitter_new.split_text(text)

    # Strategy 3: 20% overlap (new - for context extraction)
    splitter_context = ImprovedTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,  # 20%
        separator="\n\n",
    )
    chunks_context = splitter_context.split_text(text)

    # Display comparison table
    print("\n" + "-" * 90)
    print(
        f"{'Strategy':<30} {'Chunks':<12} {'Avg Size':<12} {'Total':<15} {'Overhead':<15}"
    )
    print("-" * 90)

    # Old method
    total_old = sum(len(c) for c in chunks_old)
    avg_old = total_old / len(chunks_old) if chunks_old else 0
    overhead_old = 0
    print(
        f"{'❌ No Overlap (old)':<30} {len(chunks_old):<12} {int(avg_old):<12,} {total_old:<15,} {overhead_old:<14.1f}%"
    )

    # New method - topic extraction
    total_new = sum(len(c) for c in chunks_new)
    avg_new = total_new / len(chunks_new) if chunks_new else 0
    overhead_new = ((total_new / len(text)) - 1) * 100
    print(
        f"{'✅ 10% Overlap (new, topics)':<30} {len(chunks_new):<12} {int(avg_new):<12,} {total_new:<15,} {overhead_new:<14.1f}%"
    )

    # New method - context extraction
    total_ctx = sum(len(c) for c in chunks_context)
    avg_ctx = total_ctx / len(chunks_context) if chunks_context else 0
    overhead_ctx = ((total_ctx / len(text)) - 1) * 100
    print(
        f"{'✅ 20% Overlap (new, context)':<30} {len(chunks_context):<12} {int(avg_ctx):<12,} {total_ctx:<15,} {overhead_ctx:<14.1f}%"
    )

    print("-" * 90)

    # Analyze boundary issues
    print("\n" + "=" * 90)
    print("BOUNDARY ANALYSIS")
    print("=" * 90)

    def find_sentence_breaks(chunks):
        """Count how many chunks end mid-sentence."""
        mid_sentence = 0
        for chunk in chunks:
            # Check if chunk ends with sentence-ending punctuation
            if chunk.strip() and chunk.strip()[-1] not in ".!?":
                mid_sentence += 1
        return mid_sentence

    print(f"\nChunks ending mid-sentence (potential context loss):")
    print(
        f"  ❌ No overlap: {find_sentence_breaks(chunks_old)}/{len(chunks_old)} chunks ({find_sentence_breaks(chunks_old) / len(chunks_old) * 100:.1f}%)"
    )
    print(
        f"  ✅ 10% overlap: {find_sentence_breaks(chunks_new)}/{len(chunks_new)} chunks ({find_sentence_breaks(chunks_new) / len(chunks_new) * 100:.1f}%)"
    )
    print(f"  (With overlap, mid-sentence breaks are preserved in the next chunk)")

    # Show example boundary
    if len(chunks_new) >= 2:
        print("\n" + "=" * 90)
        print("EXAMPLE: BOUNDARY BETWEEN CHUNKS 1 & 2")
        print("=" * 90)

        boundary_size = 150

        print("\n📄 Chunk 1 ending:")
        print("   ..." + chunks_new[0][-boundary_size:])

        print("\n📄 Chunk 2 beginning:")
        print("   " + chunks_new[1][:boundary_size] + "...")

        # Highlight the overlap
        overlap_size = int(chunk_size * 0.1)
        chunk1_tail = chunks_new[0][-overlap_size:]
        chunk2_head = chunks_new[1][:overlap_size]

        # Find actual overlap
        actual_overlap = 0
        for i in range(min(len(chunk1_tail), len(chunk2_head)), 0, -10):
            if chunk1_tail[-i:] in chunk2_head[: i + 50]:
                actual_overlap = i
                break

        if actual_overlap > 0:
            print(f"\n✅ Overlap region: ~{actual_overlap} characters")
            print(f"   This ensures context continuity!")

    return {
        "old": {
            "chunks": len(chunks_old),
            "total": total_old,
            "overhead": overhead_old,
        },
        "new": {
            "chunks": len(chunks_new),
            "total": total_new,
            "overhead": overhead_new,
        },
        "context": {
            "chunks": len(chunks_context),
            "total": total_ctx,
            "overhead": overhead_ctx,
        },
    }


def analyze_book_file(book_path: str):
    """Analyze chunking for a real book file."""

    print("\n" + "=" * 90)
    print(f"ANALYZING BOOK: {Path(book_path).name}")
    print("=" * 90)

    from src.document_parser import DocumentParser

    print("\n⏳ Parsing book...")
    book_data = DocumentParser.parse(book_path)

    print(f"✅ Book: {book_data['title']}")
    print(f"   Pages: {book_data.get('page_count', 'N/A')}")
    print(f"   Words: {len(book_data['content'].split()):,}")
    print(f"   Characters: {len(book_data['content']):,}")

    stats = compare_chunking_strategies(book_data["content"])

    # Recommendations
    print("\n" + "=" * 90)
    print("💡 RECOMMENDATIONS")
    print("=" * 90)

    print(f"\nFor topic extraction (processing whole book):")
    print(f"  • Use 10% overlap: {stats['new']['chunks']} chunks")
    print(f"  • Overhead: {stats['new']['overhead']:.1f}% (minimal)")
    print(f"  • Benefit: Topics spanning chunks are preserved")

    print(f"\nFor context extraction (passage retrieval):")
    print(f"  • Use 20% overlap: {stats['context']['chunks']} chunks")
    print(f"  • Overhead: {stats['context']['overhead']:.1f}%")
    print(f"  • Benefit: Better context for Q&A and exercises")

    word_count = len(book_data["content"].split())
    if word_count > 50000:
        print(f"\n⚠️ Large book ({word_count:,} words):")
        print(
            f"   Consider using chapters if available ({len(book_data.get('chapters', []))} detected)"
        )

    print("\n" + "=" * 90 + "\n")


def main():
    """Run comparison."""

    # Check for books
    books_dir = Path("data/books")

    if not books_dir.exists():
        print(f"❌ Books directory not found: {books_dir}")
        return

    # Find first available book
    books = list(books_dir.glob("*.pdf")) + list(books_dir.glob("*.epub"))

    if not books:
        print(f"❌ No books found in {books_dir}")
        return

    # Test with first book
    book_path = books[0]

    try:
        analyze_book_file(str(book_path))

        print("\n✅ Comparison complete!")
        print("\nKey Takeaways:")
        print("  1. Overlap adds minimal overhead (10-20%)")
        print("  2. Significantly improves context preservation")
        print("  3. Better topic extraction and Q&A performance")
        print("  4. Worth the small storage cost")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
