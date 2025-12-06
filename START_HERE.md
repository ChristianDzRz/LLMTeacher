# 🚀 Starting the Book Learning App

## Quick Start

### 1. Start LLM Studio First
Before running the app, make sure **LLM Studio** is running:
- Open LLM Studio
- Load a model (e.g., Mistral 7B Instruct)
- Verify it's running on `http://localhost:1234`

### 2. Run the App

**Option A: Using the startup script (Recommended)**
```bash
cd /home/christiandz/Documents/AILearning/book-learning-app
chmod +x run_app.sh
./run_app.sh
```

**Option B: Manual start with uv**
```bash
cd /home/christiandz/Documents/AILearning/book-learning-app
uv run python app.py
```

**Option C: Direct Python (if uv manages environment)**
```bash
cd /home/christiandz/Documents/AILearning/book-learning-app
python app.py
```

### 3. Open Your Browser
Navigate to: **http://localhost:5000**

---

## ✨ What's New: Improved Chunking

The app now uses **improved text chunking with overlap** for better context preservation:

- **20% overlap** for passage extraction → Better Q&A
- **10% overlap** for topic extraction → Better learning plans
- **Character-based precision** → More accurate chunking
- **Backward compatible** → All existing features work

---

## 📖 Using the App

### Upload a Book
1. Go to http://localhost:5000
2. Click "Upload Book"
3. Select a PDF or EPUB file
4. Wait for processing (may take 1-5 minutes)

### View Learning Plan
1. After upload, you'll see the extracted topics
2. Topics are now better organized thanks to improved chunking
3. Click on any topic to start studying

### Study a Topic
1. Click on a topic from the learning plan
2. Ask questions in the chat interface
3. Generate exercises to test your knowledge
4. The AI tutor has better context thanks to overlapping chunks!

---

## 🔧 Troubleshooting

### "LLM Studio not connected"
- Make sure LLM Studio is running
- Check if a model is loaded
- Verify the URL in `.env` file:
  ```
  LLM_STUDIO_URL=http://localhost:1234/v1
  ```

### "Import Error" or "Module not found"
```bash
# Sync dependencies with uv
uv sync

# Or install requirements
uv pip install -r requirements.txt
```

### "Book processing failed"
- Check the PDF/EPUB file is valid
- Try a smaller book first
- Check console for error messages
- Make sure LLM Studio is responding

### App won't start
```bash
# Check if port 5000 is already in use
lsof -i :5000  # Linux/Mac
netstat -ano | findstr :5000  # Windows

# Kill the process or use a different port
export FLASK_RUN_PORT=5001
uv run python app.py
```

---

## 📊 Test the Improved Chunking

Before processing books, you can test the chunking improvements:

```bash
# Quick demo (instant)
uv run python quick_test.py

# Analyze a real book (~30 seconds)
uv run python compare_chunking.py

# Full test with LLM (~2-5 minutes)
uv run python test_chunking.py
```

See `README_CHUNKING.md` for details.

---

## 🎯 Expected Workflow

1. **Start LLM Studio** → Load model
2. **Run the app** → `./run_app.sh` or `uv run python app.py`
3. **Upload a book** → PDF or EPUB
4. **Wait for processing** → Topics are extracted with improved chunking
5. **Study topics** → Better Q&A thanks to overlapping chunks
6. **Generate exercises** → More relevant practice questions

---

## 📁 Project Structure

```
book-learning-app/
├── app.py                    # Main Flask application
├── config.py                 # Configuration
├── requirements.txt          # Dependencies
├── .env                      # Environment variables
├── run_app.sh               # Startup script (uses uv)
├── src/
│   ├── text_splitter.py     # NEW: Improved chunking
│   ├── context_manager.py   # Updated: Uses improved chunking
│   ├── topic_extractor.py   # Updated: Uses improved chunking
│   ├── document_parser.py   # PDF/EPUB parsing
│   ├── llm_client.py        # LLM Studio integration
│   └── exercise_generator.py # Exercise generation
├── data/
│   ├── books/               # Uploaded books
│   └── processed/           # Processed book data
├── templates/               # HTML templates
└── static/                  # CSS/JS files
```

---

## 🔍 Checking if Improved Chunking is Working

After uploading a book, you can verify the improved chunking is active:

1. Check console output - should show:
   ```
   Processing X chunks with Y-word overlap...
   Extracting context with 20% overlap...
   ```

2. Ask a question that spans topics - the AI should have better context

3. Check processed files in `data/processed/` - they'll have better context data

---

## 📚 Sample Books Included

You already have some books in `data/books/`:
- Learning SQL (Alan Beaulieu)
- Ace the Data Science Interview
- SQL for Data Analysis

Try processing one of these to test the app!

---

## ⚡ Quick Commands Reference

```bash
# Start app
uv run python app.py

# Test chunking
uv run python quick_test.py

# Sync dependencies
uv sync

# Check health
curl http://localhost:5000/health

# Stop app
Ctrl + C
```

---

## 🆘 Need Help?

1. Check console output for errors
2. Verify LLM Studio is running
3. Review `README_CHUNKING.md` for chunking details
4. Check `.env` file for correct configuration
5. Run `uv sync` to ensure dependencies are installed

---

## 🎉 Ready to Start!

Everything is set up and ready. Just:

1. ✅ Start LLM Studio
2. ✅ Run `./run_app.sh` or `uv run python app.py`
3. ✅ Open http://localhost:5000
4. ✅ Upload a book and start learning!

The improved chunking will automatically provide better context for your learning experience! 🚀
