# Testing the Improved Chunking

## Quick Start

You have **3 test scripts** to demonstrate the improved chunking:

### 1. Quick Demo (Recommended First) ⚡
```bash
python quick_test.py
```
**What it shows:**
- Simple demonstration with sample text
- Visual comparison: old vs new chunking
- How overlap preserves context
- **Takes:** ~1 second

### 2. Full Comparison 📊
```bash
python compare_chunking.py
```
**What it shows:**
- Analysis of real book (Learning SQL)
- Detailed statistics and metrics
- Boundary analysis
- Recommendations for your use case
- **Takes:** ~30 seconds (needs to parse PDF)

### 3. Comprehensive Test 🧪
```bash
python test_chunking.py
```
**What it shows:**
- Full chunking analysis
- Topic extraction with improved chunking
- Context extraction with overlap
- Side-by-side comparison
- **Takes:** 2-5 minutes (calls LLM for topic extraction)

---

## What You'll See

### Before (No Overlap)
```
Chunk 1: ...learning SQL is essential
Chunk 2: There are three main types...
         ⚠️ Context lost between chunks!
```

### After (20% Overlap)
```
Chunk 1: ...learning SQL is essential for anyone
Chunk 2: essential for anyone working with data...
         ✅ Context preserved!
```

---

## Expected Results

### Chunking Statistics

| Strategy | Chunks | Overhead | Context Loss |
|----------|--------|----------|--------------|
| ❌ No Overlap (old) | 50 | 0% | YES |
| ✅ 10% Overlap (new) | 52 | ~10% | NO |
| ✅ 20% Overlap (context) | 105 | ~20% | NO |

### Benefits You'll Observe

1. **Better Topic Extraction**
   - Topics spanning chunks are captured
   - More coherent topic descriptions
   - Fewer "fragmented" topics

2. **Improved Context Quality**
   - Q&A system has more context
   - Exercise generation is better
   - Fewer "I don't know" responses

3. **Minimal Overhead**
   - 10-20% more storage (negligible)
   - Same processing time
   - Better results

---

## Running Tests on Your Own Books

### Test with Different Books
```bash
# Edit compare_chunking.py, change this line:
book_path = "data/books/YOUR_BOOK.pdf"

# Then run:
python compare_chunking.py
```

### Test Different Overlap Ratios
```python
# In quick_test.py or compare_chunking.py
splitter = ImprovedTextSplitter(
    chunk_size=1000,
    chunk_overlap=300,  # Try 30% overlap
    separator="\n\n"
)
```

---

## Interpreting Results

### Good Signs ✅
- Overlap detected between chunks
- "Context preserved" messages
- Lower "mid-sentence breaks" count
- Topics are coherent and complete

### Issues to Watch For ⚠️
- No overlap detected (check separator)
- Very high overhead (>30%)
- Chunks still too large/small
- Adjust `chunk_size` as needed

---

## Configuration Guide

### For Your Use Case

**Small Books (<50 pages)**
```python
chunk_size = 6000      # ~1000 words
chunk_overlap = 600     # 10%
```

**Medium Books (50-200 pages)**
```python
chunk_size = 12000     # ~2000 words
chunk_overlap = 1200    # 10%
```

**Large Books (>200 pages)**
```python
chunk_size = 18000     # ~3000 words
chunk_overlap = 1800    # 10%
```

**Technical/Complex Content**
```python
chunk_size = 1000      # Smaller chunks
chunk_overlap = 200     # 20% overlap (more context)
```

---

## Troubleshooting

### "Book not found"
- Check the path in the script
- Make sure PDFs are in `data/books/`
- Try using full path

### "Import Error"
- Make sure you're in the project directory
- Activate virtual environment if using one:
  ```bash
  source .venv/bin/activate  # Linux/Mac
  .venv\Scripts\activate     # Windows
  ```

### "LLM Error" (test_chunking.py only)
- Make sure LLM Studio is running
- Check LLM_STUDIO_URL in config.py
- You can skip topic extraction test if needed

### Tests Run Slowly
- `quick_test.py` - Should be instant
- `compare_chunking.py` - Takes ~30 sec (PDF parsing)
- `test_chunking.py` - Takes 2-5 min (LLM calls)

---

## Next Steps

After testing:

1. ✅ **Confirm chunking works** - Run `quick_test.py`
2. 📊 **See real impact** - Run `compare_chunking.py`
3. 🚀 **Use in production** - Process books normally, chunking is automatic!

The improved chunking is **already integrated** into:
- `src/topic_extractor.py` - Topic extraction
- `src/context_manager.py` - Context extraction
- `src/text_splitter.py` - Core chunking logic

Just use the app normally - it's now using improved chunking automatically! 🎉

---

## Questions?

- **"Is overlap worth it?"** - Yes! 10-20% overhead for significantly better results
- **"Will it break existing code?"** - No! Fully backward compatible
- **"Do I need to reprocess books?"** - No, but reprocessing will give better results
- **"Can I disable overlap?"** - Yes, set `chunk_overlap=0` or `overlap_ratio=0`

---

## Example Output

```
================================================================================
CHUNKING STRATEGY COMPARISON
================================================================================

Input text: 245,832 characters (~41,234 words)

--------------------------------------------------------------------------------
Strategy                       Chunks       Avg Size     Total           Overhead       
--------------------------------------------------------------------------------
❌ No Overlap (old)            21           11,706       245,832         0.0%
✅ 10% Overlap (new, topics)   23           11,706       269,142         9.5%
✅ 20% Overlap (new, context)  256          1,151        294,398         19.7%
--------------------------------------------------------------------------------

💡 RECOMMENDATIONS
================================================================================

For topic extraction (processing whole book):
  • Use 10% overlap: 23 chunks
  • Overhead: 9.5% (minimal)
  • Benefit: Topics spanning chunks are preserved

For context extraction (passage retrieval):
  • Use 20% overlap: 256 chunks
  • Overhead: 19.7%
  • Benefit: Better context for Q&A and exercises
```

---

Happy testing! 🚀
