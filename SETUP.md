# Book Learning App - Setup Guide

## Prerequisites

1. **Python 3.8+** installed
2. **uv** package manager (recommended)
   - Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Or use pip if you prefer
3. **LLM Studio** installed and running
   - Download from: https://lmstudio.ai/
   - Load a model (recommended: Mistral 7B or similar)
   - Start the local server (default: http://localhost:1234)

## Installation Steps

### 1. Install Dependencies

Using **uv** (recommended):

```bash
cd book-learning-app
uv sync
```

Or using **pip**:

```bash
cd book-learning-app
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file (or copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env`:

```
SECRET_KEY=your-secret-key-here
DEBUG=True

# LLM Studio Configuration
LLM_STUDIO_URL=http://localhost:1234/v1
LLM_MODEL=local-model
```

### 3. Verify LLM Studio Connection

Make sure LLM Studio is running and has a model loaded.

Test the connection:

```bash
uv run src/llm_client.py
```

You should see:
```
Testing LLM Studio connection...
✓ Connection successful!
```

### 4. Run the Application

```bash
uv run app.py
```

The app will start at: **http://localhost:5000**

## Usage

### 1. Upload a Book

- Go to http://localhost:5000
- Click "Choose a book (PDF or EPUB)"
- Select a PDF or EPUB file
- Click "Upload and Process"
- Wait for processing (may take 1-5 minutes depending on book size)

### 2. View Learning Plan

- After processing, you'll be redirected to the learning plan
- You'll see 8-15 key topics extracted from the book
- Each topic shows:
  - Title
  - Description
  - Importance level (High/Medium/Low)

### 3. Study a Topic

- Click "Start Learning" on any topic
- Chat with the AI tutor about the topic
- Ask questions, request explanations, discuss concepts
- The AI has context from the relevant parts of the book

### 4. Practice with Exercises

- Click "Generate Exercises" in the sidebar
- Work through conceptual and practical exercises
- Submit answers and get feedback

## Testing Individual Components

### Test Document Parser

```bash
uv run src/document_parser.py path/to/your/book.pdf
```

### Test Topic Extraction

```bash
uv run src/topic_extractor.py path/to/your/book.pdf
```

This will:
1. Parse the book
2. Extract key topics
3. Save processed data to `data/processed/`
4. Display the learning plan

### Test Context Extraction

```bash
# After processing a book
uv run src/context_manager.py data/processed/Your_Book.json
```

Add `--llm` flag to use LLM-based context extraction (slower but more accurate):

```bash
uv run src/context_manager.py data/processed/Your_Book.json --llm
```

### Test Exercise Generation

```bash
# After extracting contexts
uv run src/exercise_generator.py data/processed/Your_Book_contexts.json
```

## Troubleshooting

### LLM Studio Connection Issues

**Error:** "Connection failed"

**Solutions:**
1. Make sure LLM Studio is running
2. Check that a model is loaded in LLM Studio
3. Verify the server is running (look for "Server running on port 1234")
4. Check the URL in `.env` matches LLM Studio's server URL
5. Try accessing http://localhost:1234/v1/models in your browser

### Book Processing Fails

**Error:** "Processing failed"

**Solutions:**
1. Check the PDF/EPUB is valid and not corrupted
2. Ensure the file is not password-protected
3. Try a different book to isolate the issue
4. Check console output for specific errors

### Slow Processing

**Tips:**
- Large books (500+ pages) may take 3-5 minutes
- Topic extraction requires multiple LLM calls
- Context extraction with `--llm` flag is slower but more accurate
- Default uses keyword-based context extraction (faster)

### Out of Memory

For very large books:
1. The app automatically chunks content
2. Reduce `max_chunk_words` in `topic_extractor.py`
3. Use a model with larger context window

## Configuration Options

### LLM Settings

Edit `config.py` to adjust:

```python
# LLM Studio URL
LLM_STUDIO_URL = 'http://localhost:1234/v1'

# Model name (usually 'local-model' for LLM Studio)
LLM_MODEL = 'local-model'
```

### File Upload Limits

```python
# Maximum file size (bytes)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Allowed file types
ALLOWED_EXTENSIONS = {'pdf', 'epub'}
```

### Context Window

Adjust context size for each topic in `app.py`:

```python
context[:4000]  # Limit to 4000 characters
```

## Architecture Overview

```
User → Flask App → Document Parser → Book Text
                ↓
        Topic Extractor → LLM → Learning Plan (8-15 topics)
                ↓
        Context Manager → Extract relevant passages per topic
                ↓
        Study Session → Conversation Manager → LLM Tutor
                ↓
        Exercise Generator → LLM → Practice Problems
```

## API Endpoints

- `GET /` - Upload page
- `POST /upload` - Upload and process book
- `GET /learning-plan` - View topics
- `GET /study/<topic_id>` - Study interface
- `POST /api/chat` - Send chat message
- `POST /api/generate-exercises/<topic_id>` - Generate exercises
- `GET /health` - Health check

## Development

### Project Structure

```
book-learning-app/
├── app.py                      # Main Flask application
├── config.py                   # Configuration
├── src/                        # Core modules
│   ├── document_parser.py      # PDF/EPUB parsing
│   ├── llm_client.py          # LLM integration
│   ├── topic_extractor.py     # Topic extraction
│   ├── context_manager.py     # Context extraction
│   └── exercise_generator.py  # Exercise creation
├── templates/                  # HTML templates
├── static/                     # CSS/JS
└── data/                      # Storage
    ├── books/                 # Uploaded books
    └── processed/             # Processed data
```

### Adding Features

1. **Custom prompts:** Edit `src/llm_client.py` → `PromptTemplates`
2. **UI changes:** Edit `templates/` and `static/css/style.css`
3. **New routes:** Add to `app.py`
4. **Database:** Replace JSON storage with SQLite/PostgreSQL

## Next Steps

1. Upload your first book
2. Explore the generated learning plan
3. Try studying a topic with the AI tutor
4. Generate and complete exercises
5. Experiment with different books and subjects

## Support

For issues or questions:
- Check console output for errors
- Test individual components separately
- Verify LLM Studio is working properly
- Try with a smaller book first

Happy learning!
