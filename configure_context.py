#!/usr/bin/env python3
"""
Configure chunk size based on LM Studio context window.

Run this after changing your context length in LM Studio.
"""

import sys
from pathlib import Path


def configure_chunks(context_tokens: int):
    """
    Configure chunk sizes based on available context window.

    Args:
        context_tokens: Context window size (4096, 8192, 16384, etc.)
    """

    # Calculate safe chunk size (leave room for prompt + response)
    # Use ~40% of context for input chunk, rest for system prompt + response
    usable_tokens = int(context_tokens * 0.4)

    # Convert tokens to words (rough: 1 token ≈ 0.75 words)
    chunk_words = int(usable_tokens * 0.75)
    overlap_words = int(chunk_words * 0.1)  # 10% overlap

    print(f"Context window: {context_tokens} tokens")
    print(f"Usable for chunks: {usable_tokens} tokens (~{chunk_words} words)")
    print(f"Chunk size: {chunk_words} words")
    print(f"Overlap: {overlap_words} words (10%)")
    print()

    # Update topic_extractor.py
    file_path = Path("src/topic_extractor.py")
    content = file_path.read_text()

    # Find and replace chunk_text defaults
    import re

    # Replace max_words default in chunk_text
    content = re.sub(
        r"def chunk_text\(\s*text: str, max_words: int = \d+, overlap_words: int = \d+",
        f"def chunk_text(\n        text: str, max_words: int = {chunk_words}, overlap_words: int = {overlap_words}",
        content,
    )

    # Replace max_chunk_words default in extract_topics
    content = re.sub(
        r"max_chunk_words: int = \d+,",
        f"max_chunk_words: int = {chunk_words},",
        content,
    )

    file_path.write_text(content)
    print(f"✅ Updated src/topic_extractor.py")
    print(f"   • Chunk size: {chunk_words} words")
    print(f"   • Overlap: {overlap_words} words")

    return chunk_words, overlap_words


def main():
    print("=" * 70)
    print("CONFIGURE CHUNK SIZE FOR YOUR CONTEXT WINDOW")
    print("=" * 70)
    print()

    # Get context size from user
    if len(sys.argv) > 1:
        try:
            context_tokens = int(sys.argv[1])
        except ValueError:
            print("❌ Error: Please provide a valid number")
            sys.exit(1)
    else:
        print("What context length did you set in LM Studio?")
        print()
        print("Common options:")
        print("  1. 4096  - Default (small)")
        print("  2. 8192  - Recommended for RTX 3070")
        print("  3. 16384 - Large contexts")
        print("  4. 32768 - Very large (slower)")
        print()

        choice = input("Enter context length (or press Enter for 8192): ").strip()

        if not choice:
            context_tokens = 8192
        else:
            try:
                context_tokens = int(choice)
            except ValueError:
                print("❌ Invalid input, using 8192")
                context_tokens = 8192

    print()
    chunk_words, overlap = configure_chunks(context_tokens)

    print()
    print("=" * 70)
    print("✅ CONFIGURATION COMPLETE!")
    print()
    print("Next steps:")
    print("  1. Make sure LM Studio is configured with the same context length")
    print("  2. Reload your model in LM Studio")
    print("  3. Restart the app: uv run python app.py")
    print()
    print(f"With {context_tokens} tokens, your book will be processed in fewer,")
    print(f"larger chunks ({chunk_words} words each) with better context!")
    print("=" * 70)


if __name__ == "__main__":
    main()
