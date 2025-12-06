#!/usr/bin/env python3
"""
Add error resilience to topic extraction - don't fail on single chunk errors.
"""

from pathlib import Path


def add_resilience():
    """Add try-catch blocks and failure tracking to _extract_topics_from_chunks"""

    file_path = Path("src/topic_extractor.py")
    content = file_path.read_text()

    # Find the _extract_topics_from_chunks method and update it
    old_code = """        print(f"Processing {len(chunks)} chunks with {overlap_words}-word overlap...")

        all_chunk_topics = []

        for i, chunk in enumerate(chunks, 1):
            print(f"Processing chunk {i}/{len(chunks)}...")

            chunk_topics = self._extract_topics_single(
                chunk, f"{book_title} (Part {i})"
            )
            all_chunk_topics.extend(chunk_topics)

        # Merge and refine topics
        print("Merging topics from all chunks...")
        final_topics = self._merge_topics(all_chunk_topics, book_title)

        return final_topics"""

    new_code = """        print(f"Processing {len(chunks)} chunks with {overlap_words}-word overlap...")

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
            print(f"\n⚠️  Warning: {len(failed_chunks)}/{len(chunks)} chunks failed to process")
            print(f"  Failed chunks: {', '.join(map(str, failed_chunks))}")
            print(f"  Successfully processed: {len(chunks) - len(failed_chunks)}/{len(chunks)} chunks")
        else:
            print(f"\n✅ All {len(chunks)} chunks processed successfully!")

        # Check if we got any topics at all
        if not all_chunk_topics:
            raise Exception(f"Failed to extract topics from any chunks. All {len(chunks)} chunks failed.")

        # Merge and refine topics
        print("Merging topics from all chunks...")
        final_topics = self._merge_topics(all_chunk_topics, book_title)

        return final_topics"""

    if old_code in content:
        content = content.replace(old_code, new_code)
        file_path.write_text(content)
        print("✅ Added error resilience to _extract_topics_from_chunks")
        print("   • Failed chunks won't stop processing")
        print("   • Failure tracking added")
        print("   • Summary report at end")
        return True
    else:
        print("⚠️  Could not find code to replace (may already be updated)")
        return False


def add_context_manager_resilience():
    """Add error resilience to context extraction"""

    file_path = Path("src/context_manager.py")

    if not file_path.exists():
        print("⚠️  context_manager.py not found, skipping")
        return False

    content = file_path.read_text()

    # Add resilience to build_topic_contexts
    old_code = """        for i, topic in enumerate(topics, 1):
            print(f"\nExtracting context for topic {i}/{len(topics)}: {topic['title']}")

            context_data = self.extract_relevant_context(
                topic, book_content, max_context_words=3000, use_llm=use_llm
            )

            topic_contexts[topic["topic_number"]] = context_data

            print(
                f"  → Extracted {context_data['word_count']} words using {context_data['method']} method"
            )

        return topic_contexts"""

    new_code = """        failed_topics = []

        for i, topic in enumerate(topics, 1):
            print(f"\nExtracting context for topic {i}/{len(topics)}: {topic['title']}")

            try:
                context_data = self.extract_relevant_context(
                    topic, book_content, max_context_words=3000, use_llm=use_llm
                )

                topic_contexts[topic["topic_number"]] = context_data

                print(
                    f"  → Extracted {context_data['word_count']} words using {context_data['method']} method"
                )
            except Exception as e:
                print(f"  ⚠️  ERROR extracting context for topic {i}: {e}")
                print(f"  → Continuing with remaining topics...")
                failed_topics.append(topic["topic_number"])
                continue

        # Report failures
        if failed_topics:
            print(f"\n⚠️  Warning: Failed to extract context for {len(failed_topics)}/{len(topics)} topics")
            print(f"  Failed topics: {', '.join(map(str, failed_topics))}")
        else:
            print(f"\n✅ Successfully extracted context for all {len(topics)} topics!")

        return topic_contexts"""

    if old_code in content:
        content = content.replace(old_code, new_code)
        file_path.write_text(content)
        print("✅ Added error resilience to context_manager.py")
        print("   • Failed context extractions won't stop processing")
        return True
    else:
        print("⚠️  Could not find code to replace in context_manager.py")
        return False


def main():
    print("=" * 70)
    print("ADDING ERROR RESILIENCE TO BOOK PROCESSING")
    print("=" * 70)
    print()
    print("This will make the app continue processing even if some chunks fail.")
    print()

    success1 = add_resilience()
    print()
    success2 = add_context_manager_resilience()

    print()
    print("=" * 70)

    if success1 or success2:
        print("✅ ERROR RESILIENCE ADDED!")
        print()
        print("Benefits:")
        print("  • Chunk processing failures won't kill the entire process")
        print("  • Failed chunks are tracked and reported")
        print("  • You get partial results even if some chunks fail")
        print("  • Better visibility into what succeeded/failed")
        print()
        print("Try processing a book again - it should be more robust!")
    else:
        print("⚠️  No changes made (may already be applied)")

    print("=" * 70)


if __name__ == "__main__":
    main()
