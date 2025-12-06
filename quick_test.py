"""
Quick test to see improved chunking in action.
Run this to see how the new chunking preserves context.
"""

from src.text_splitter import ImprovedTextSplitter

# Sample text that simulates a book chapter
sample_text = """
SQL, or Structured Query Language, is the standard language for interacting with relational databases. Understanding SQL is essential for anyone working with data, from data analysts to database administrators.

The foundation of SQL lies in its ability to perform four main operations, commonly known as CRUD: Create, Read, Update, and Delete. These operations allow you to manage data within database tables effectively.

Creating tables is the first step in building a database schema. Tables consist of columns that define the structure and rows that contain the actual data. Each column has a specific data type such as VARCHAR for text or INTEGER for numbers.

Reading data is performed using the SELECT statement, which is the most frequently used SQL command. SELECT allows you to retrieve specific columns from tables and filter results using WHERE clauses.

The WHERE clause is crucial for filtering data. It allows you to specify conditions that rows must meet to be included in the result set. For example, you might want to find all customers from a specific city.

Joining tables is another fundamental concept in SQL. Joins combine data from multiple tables based on related columns, allowing you to create comprehensive result sets from normalized database structures.

There are several types of joins in SQL: INNER JOIN returns only matching rows from both tables, LEFT JOIN returns all rows from the left table and matching rows from the right, and FULL OUTER JOIN returns all rows from both tables.

Understanding join types is critical for writing efficient queries. The wrong join type can lead to unexpected results or poor performance, especially with large datasets.

Aggregate functions like COUNT, SUM, AVG, MIN, and MAX allow you to perform calculations on groups of rows. These functions are essential for generating summary statistics and reports from your data.

The GROUP BY clause works hand-in-hand with aggregate functions. It divides the result set into groups and allows you to apply aggregate functions to each group independently.
"""

print("\n" + "=" * 80)
print("IMPROVED CHUNKING DEMONSTRATION")
print("=" * 80)

print(
    f"\nOriginal text: {len(sample_text)} characters, {len(sample_text.split())} words"
)

# Test 1: Without overlap (old way)
print("\n" + "-" * 80)
print("❌ OLD METHOD: No Overlap")
print("-" * 80)

old_splitter = ImprovedTextSplitter(
    chunk_size=500,
    chunk_overlap=0,  # NO OVERLAP
    separator="\n\n",
)

old_chunks = old_splitter.split_text(sample_text)
print(f"Chunks created: {len(old_chunks)}")

for i, chunk in enumerate(old_chunks, 1):
    words = chunk.split()
    print(f"\nChunk {i}: {len(chunk)} chars, {len(words)} words")
    print(f"  Ends with: ...{' '.join(words[-10:])}")
    if i < len(old_chunks):
        next_words = old_chunks[i].split()
        print(f"  Next starts: {' '.join(next_words[:10])}...")
        print(f"  ⚠️ No overlap - context is lost between chunks!")

# Test 2: With overlap (new way)
print("\n" + "-" * 80)
print("✅ NEW METHOD: 20% Overlap")
print("-" * 80)

new_splitter = ImprovedTextSplitter(
    chunk_size=500,
    chunk_overlap=100,  # 20% OVERLAP
    separator="\n\n",
)

new_chunks = new_splitter.split_text(sample_text)
print(f"Chunks created: {len(new_chunks)}")

for i, chunk in enumerate(new_chunks, 1):
    words = chunk.split()
    print(f"\nChunk {i}: {len(chunk)} chars, {len(words)} words")
    print(f"  Ends with: ...{' '.join(words[-10:])}")
    if i < len(new_chunks):
        next_words = new_chunks[i].split()
        print(f"  Next starts: {' '.join(next_words[:10])}...")

        # Check for overlap
        chunk_end = " ".join(words[-15:])
        chunk_next_start = " ".join(next_words[:15])

        # Find common words
        common = []
        for word in words[-15:]:
            if word in next_words[:15]:
                common.append(word)

        if common:
            print(f"  ✅ Overlap detected! Common words: {', '.join(common[:5])}...")

# Show actual overlap
print("\n" + "-" * 80)
print("OVERLAP VISUALIZATION")
print("-" * 80)

if len(new_chunks) >= 2:
    print("\n📄 Chunk 1 ending (last 100 chars):")
    print(f"   ...{new_chunks[0][-100:]}")

    print("\n📄 Chunk 2 beginning (first 100 chars):")
    print(f"   {new_chunks[1][:100]}...")

    # Find exact overlap
    for length in range(100, 0, -5):
        if new_chunks[0][-length:] == new_chunks[1][:length]:
            print(f"\n✅ Exact overlap: {length} characters")
            print(f"   '{new_chunks[0][-length:][:80]}...'")
            break

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

total_old = sum(len(c) for c in old_chunks)
total_new = sum(len(c) for c in new_chunks)
overhead = (total_new / len(sample_text) - 1) * 100

print(f"\nOld method (no overlap):")
print(f"  • Chunks: {len(old_chunks)}")
print(f"  • Total chars: {total_old}")
print(f"  • Context loss at boundaries: YES ❌")

print(f"\nNew method (20% overlap):")
print(f"  • Chunks: {len(new_chunks)}")
print(f"  • Total chars: {total_new}")
print(f"  • Overhead: {overhead:.1f}%")
print(f"  • Context preserved at boundaries: YES ✅")

print(f"\n💡 Key Benefit: With overlap, concepts spanning chunk boundaries")
print(f"   are preserved in both chunks, improving LLM understanding!")

print("\n" + "=" * 80 + "\n")
