# Text Chunking Improvements

## Overview

This document describes the improved text chunking strategy implemented based on best practices from:
- LangChain's CharacterTextSplitter
- DocMind AI's chunking strategies  
- GeeksforGeeks LLM PDF summarizer patterns

## What Changed

### Before: Simple Paragraph-Based Chunking
- No overlap between chunks
- Lost context at chunk boundaries
- Word-based sizing (imprecise)
- Potential information loss when topics span chunks

### After: Improved Chunking with Overlap
- **20% overlap** between chunks (configurable)
- **Context preservation** across chunk boundaries
- **Character-based sizing** for precision
- **Semantic boundaries** respected (paragraphs first, then sentences)

## Key Features

### 1. Configurable Overlap
```python
# Default: 20% overlap for context preservation
splitter = ImprovedTextSplitter(
    chunk_size=1000,      # characters
    chunk_overlap=200     # 20% overlap
)
```

**Why 20% overlap?**
- Based on GeeksforGeeks recommendation (1000 chars, 200 overlap)
- Maintains context across boundaries
- Prevents topic fragmentation
- Minimal redundancy overhead

### 2. Semantic Boundary Preservation
- Splits on **paragraph boundaries** first (`\n\n`)
- Falls back to **sentence boundaries** for large paragraphs
- Avoids breaking mid-sentence or mid-paragraph

### 3. Character-Based Sizing
- More precise than word-based counting
- Consistent with token limits (approximate 4 chars per token)
- Better alignment with LLM context windows

## Usage Examples

### Context Manager (Passage Splitting)
```python
from src.context_manager import ContextManager

manager = ContextManager()

# Automatically uses improved chunking with 20% overlap
passages = manager.split_into_passages(
    text=book_content,
    passage_size=1000,      # characters
    overlap_ratio=0.2       # 20% overlap
)

# Returns: List[(passage_text, start_position)]
```

### Topic Extractor (Book Chunking)
```python
from src.topic_extractor import TopicExtractor

extractor = TopicExtractor()

# Automatically uses improved chunking with 10% overlap
chunks = extractor.chunk_text(
    text=book_content,
    max_words=2000,         # converted to ~12,000 chars
    overlap_words=200       # 10% overlap, converted to ~1,200 chars
)

# Returns: List[chunk_text]
```

### Direct Text Splitter Usage
```python
from src.text_splitter import ImprovedTextSplitter

# Basic usage
splitter = ImprovedTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separator="\n\n"
)

chunks = splitter.split_text(book_content)

# With position tracking
chunks_with_positions = splitter.split_text_with_positions(book_content)
# Returns: List[(chunk_text, start_position)]
```

### Semantic Text Splitter
```python
from src.text_splitter import SemanticTextSplitter

# Respects paragraph > sentence > word boundaries
splitter = SemanticTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

chunks = splitter.split_text(book_content)
```

## Performance Impact

### Benefits
✅ **Better context preservation** - Topics spanning chunks are better preserved  
✅ **Improved LLM understanding** - More context in each chunk  
✅ **Better retrieval accuracy** - Overlapping content improves search results  
✅ **Reduced information loss** - Less fragmentation of concepts  

### Trade-offs
⚠️ **Slight increase in storage** - ~20% more data due to overlap  
⚠️ **Slightly more processing** - More chunks to process (marginal)  
⚠️ **Duplicate content** - Some text appears in multiple chunks (by design)

## Configuration Guidelines

### Chunk Size Selection

| Use Case | Chunk Size | Overlap | Reasoning |
|----------|------------|---------|-----------|
| Context extraction | 1000 chars | 200 (20%) | Good for passage retrieval |
| Topic extraction | 12,000 chars (2000 words) | 1,200 (10%) | Fits LLM context, preserves topics |
| Large documents | 6,000 chars (1000 words) | 600 (10%) | Balance between size and context |
| Fine-grained search | 500 chars | 100 (20%) | Detailed retrieval, more overlap needed |

### Overlap Ratio Guidelines

- **10%**: Minimal overlap, good for very large documents
- **20%**: Recommended default, good balance
- **30%+**: Maximum context preservation, use for complex/technical content

## Best Practices

### 1. Choose Appropriate Chunk Size
```python
# For LLM processing (stay under context limit)
chunk_size = 12000  # ~3000 tokens (for 4096 token models)

# For vector storage/retrieval
chunk_size = 1000   # Smaller chunks, better search granularity
```

### 2. Adjust Overlap Based on Content
```python
# Technical/complex content: Higher overlap
overlap_ratio = 0.3  # 30%

# Narrative/simple content: Lower overlap  
overlap_ratio = 0.1  # 10%

# Default: Balanced
overlap_ratio = 0.2  # 20%
```

### 3. Use Semantic Splitter for Narrative Text
```python
# For stories, essays, articles
splitter = SemanticTextSplitter(chunk_size=1000, chunk_overlap=200)

# For structured/technical content
splitter = ImprovedTextSplitter(chunk_size=1000, chunk_overlap=200)
```

## Implementation Details

### How Overlap Works

```
Chunk 1: [--------------------]
                        [--------------------] Chunk 2
                                        [--------------------] Chunk 3
         ^              ^
         |              |
    Main content    Overlap (20%)
```

- Each chunk includes the last 20% of the previous chunk
- Overlap starts at natural boundaries (paragraph/sentence) when possible
- Ensures concepts spanning boundaries are captured in both chunks

### Word-to-Character Conversion

The system uses an approximate conversion:
- **1 word ≈ 6 characters** (5 char word + 1 space)
- **1 token ≈ 4 characters** (for English text)

Example:
```python
max_words = 2000
# Converts to: 2000 * 6 = 12,000 characters
# Approximately: 12,000 / 4 = 3,000 tokens
```

## Testing

To test the improved chunking:

```bash
# Test text splitter directly
python src/text_splitter.py

# Test with book processing
python src/topic_extractor.py path/to/book.pdf

# Test context extraction
python src/context_manager.py processed/book.json --llm
```

## Migration Notes

### Backward Compatibility
✅ All existing code continues to work  
✅ Function signatures unchanged (overlap is optional parameter)  
✅ Default behavior improved (automatic overlap enabled)

### No Breaking Changes
- `split_into_passages()` - Now includes overlap (20% default)
- `chunk_text()` - Now includes overlap (10% default)
- Existing code gets improvements automatically

## References

1. **LangChain CharacterTextSplitter**
   - Separator-based splitting
   - Configurable chunk size and overlap
   - Character-level precision

2. **GeeksforGeeks PDF Summarizer**
   - 1000 character chunks
   - 200 character overlap (20%)
   - Paragraph-based separation

3. **DocMind AI**
   - Late chunking for better context
   - Multi-vector embeddings
   - Hybrid retrieval strategies

## Future Enhancements

Potential improvements to consider:

1. **Late Chunking** - Embed first, then chunk (from DocMind AI)
2. **Hybrid Retrieval** - Combine dense + sparse embeddings
3. **Adaptive Overlap** - Adjust overlap based on content complexity
4. **Token-Aware Chunking** - Use actual tokenizer instead of approximation
5. **Metadata Preservation** - Track chunk metadata (chapter, section, etc.)
