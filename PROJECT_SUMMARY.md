# Book Learning App - Project Summary

## Overview

A conversational AI-powered learning platform that transforms books into structured, interactive learning experiences using local LLM models.

## What It Does

1. **Book Analysis** - Upload PDF/EPUB books
2. **Topic Extraction** - AI analyzes and creates 8-15 key learning topics
3. **Conversational Tutoring** - Chat with AI about each topic like talking to an expert
4. **Exercise Generation** - Create practice problems to reinforce learning
5. **Progress Tracking** - Mark topics complete as you learn

## Key Features

### Smart Learning Plan
- AI identifies the most important concepts from any book
- Organizes topics in logical learning progression
- Prioritizes by importance (High/Medium/Low)

### Conversational Learning
- Natural dialogue with AI tutor
- Ask questions, request examples, discuss concepts
- AI has context from relevant book sections
- Identifies and fills knowledge gaps

### Adaptive Exercises
- Generates custom exercises per topic
- Mix of conceptual questions and practical problems
- Hints and feedback included
- Validates answers with constructive feedback

### Local & Private
- Runs entirely on your computer
- Uses LLM Studio (local models)
- No data sent to external servers
- Full control over your learning data

## Architecture

```
┌─────────────┐
│  User       │
│  Uploads    │
│  Book       │
└─────┬───────┘
      │
      ▼
┌─────────────────────┐
│ Document Parser     │ ◄─── Extracts text from PDF/EPUB
│ (PyPDF2/pdfplumber) │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Topic Extractor     │ ◄─── AI analyzes book
│ (LLM)              │      Creates learning plan
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Context Manager     │ ◄─── Extracts relevant passages
│                     │      for each topic
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────────┐
│           Study Session             │
│  ┌─────────────────────────────┐   │
│  │ Conversation Manager        │   │ ◄─── User chats with AI tutor
│  │ (Manages chat history)      │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ Exercise Generator          │   │ ◄─── Creates practice problems
│  │ (LLM)                       │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

## Technology Stack

### Backend
- **Python 3.8+**
- **Flask** - Web framework
- **PyPDF2 / pdfplumber** - PDF parsing
- **EbookLib** - EPUB parsing
- **Requests** - API calls

### Frontend
- **HTML5** - Structure
- **CSS3** - Styling (custom, no frameworks)
- **Vanilla JavaScript** - Interactivity

### AI/LLM
- **LLM Studio** - Local model hosting
- **OpenAI-compatible API** - Communication
- Supports any LLM Studio model (Mistral, Llama, etc.)

## Project Structure

```
book-learning-app/
├── app.py                      # Main Flask application & routes
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── test_setup.py              # Setup verification script
│
├── src/                        # Core backend modules
│   ├── document_parser.py      # PDF/EPUB text extraction
│   ├── llm_client.py          # LLM Studio integration
│   ├── topic_extractor.py     # Learning topic extraction
│   ├── context_manager.py     # Relevant content extraction
│   └── exercise_generator.py  # Practice problem creation
│
├── templates/                  # HTML templates
│   ├── base.html              # Base template
│   ├── upload.html            # Book upload page
│   ├── learning_plan.html     # Topics overview
│   └── study.html             # Study/chat interface
│
├── static/                     # Frontend assets
│   ├── css/style.css          # Styling
│   └── js/main.js             # JavaScript utilities
│
├── data/                       # Data storage
│   ├── books/                 # Uploaded books
│   └── processed/             # Processed book data (JSON)
│
└── docs/
    ├── README.md              # Project overview
    ├── QUICKSTART.md          # 5-minute setup
    ├── SETUP.md               # Detailed setup guide
    └── PROJECT_SUMMARY.md     # This file
```

## Core Components

### 1. Document Parser (`src/document_parser.py`)
- Extracts text from PDF and EPUB files
- Handles metadata (title, author, etc.)
- Provides statistics (word count, pages)
- Robust error handling for various formats

### 2. LLM Client (`src/llm_client.py`)
- Communicates with LLM Studio
- Manages conversations with history
- Pre-built prompt templates for different tasks
- Connection testing and error handling

### 3. Topic Extractor (`src/topic_extractor.py`)
- Analyzes book content with AI
- Extracts 8-15 key learning topics
- Handles large books via chunking
- Merges topics from multiple chunks
- Saves structured learning plans

### 4. Context Manager (`src/context_manager.py`)
- Finds relevant book passages for each topic
- Two methods: keyword-based (fast) or LLM-based (accurate)
- Splits book into manageable passages
- Ranks passages by relevance

### 5. Exercise Generator (`src/exercise_generator.py`)
- Creates practice problems for topics
- Multiple exercise types (conceptual, application, practical)
- Includes hints and difficulty levels
- Can validate user answers with feedback

### 6. Flask App (`app.py`)
- Routes for upload, learning plan, study sessions
- API endpoints for chat and exercise generation
- Session management for conversations
- Health check endpoint

## Data Flow

### Book Processing Flow
1. User uploads PDF/EPUB → Saved to `data/books/`
2. Document Parser extracts text
3. Topic Extractor sends to LLM → Generates learning plan
4. Context Manager extracts relevant passages per topic
5. All data saved to `data/processed/<book_name>.json`

### Study Session Flow
1. User selects topic from learning plan
2. App loads topic + relevant context
3. Creates conversation with system prompt (tutor persona)
4. User asks questions → Sent to LLM with context
5. AI responds → Displayed in chat
6. Conversation history maintained

### Exercise Flow
1. User clicks "Generate Exercises"
2. App sends topic + context to LLM
3. LLM creates 5 exercises (various types)
4. Exercises displayed in sidebar
5. User works through exercises
6. Can submit for validation (optional)

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | / | Upload page |
| POST | /upload | Upload & process book |
| GET | /learning-plan | View topics |
| GET | /study/<topic_id> | Study interface |
| POST | /api/chat | Send chat message |
| POST | /api/generate-exercises/<id> | Generate exercises |
| POST | /api/clear-conversation/<id> | Clear chat history |
| GET | /health | Health check |

## Customization Points

### 1. Prompts
Edit `src/llm_client.py` → `PromptTemplates` class
- Modify tutoring style
- Adjust exercise types
- Change topic extraction criteria

### 2. Number of Topics
Edit `src/llm_client.py` → `topic_extraction_prompt()`
- Change from "8-15 topics" to your preferred range

### 3. Context Size
Edit `app.py` → `study_topic()` function
- Adjust `context[:4000]` to change context window

### 4. Exercise Count
Edit `src/exercise_generator.py` or route
- Change `num_exercises=5` parameter

### 5. Styling
Edit `static/css/style.css`
- Customize colors, fonts, layouts
- All CSS variables in `:root`

### 6. Processing Speed
Edit `app.py` → `upload_book()`
- Change `use_llm=False` to `True` for better context extraction (slower)

## Strengths

1. **Fully Local** - Complete privacy, no external APIs
2. **Model Agnostic** - Works with any LLM Studio model
3. **Conversational** - Natural dialogue vs. static content
4. **Adaptive** - Context-aware responses
5. **Comprehensive** - Full learning workflow (study + practice)
6. **Extensible** - Modular architecture, easy to enhance
7. **No Database Required** - Simple JSON storage

## Future Enhancements

Possible additions:
- [ ] Multi-user support with database
- [ ] Progress persistence & analytics
- [ ] Flashcard generation
- [ ] Audio explanations (TTS)
- [ ] Spaced repetition scheduling
- [ ] Book annotations & highlights
- [ ] Export study notes
- [ ] Compare multiple books on same topic
- [ ] Collaborative learning (share topics)
- [ ] Mobile-responsive design improvements

## Performance Characteristics

### Processing Times (approximate)
- Small book (50-100 pages): 1-2 minutes
- Medium book (100-300 pages): 2-4 minutes
- Large book (300-500 pages): 4-7 minutes

### Memory Usage
- Base app: ~100-200 MB
- Processing book: +200-500 MB (depending on size)
- Active conversation: +50-100 MB

### LLM Requirements
- Minimum: 7B parameter model (Mistral 7B)
- Recommended: 8B+ parameter model (Llama 3.1 8B)
- RAM: 8GB+ for smooth operation

## Testing

Run setup test:
```bash
uv run test_setup.py
```

Test individual components:
```bash
# Document parsing
uv run src/document_parser.py book.pdf

# Topic extraction
uv run src/topic_extractor.py book.pdf

# Context extraction
uv run src/context_manager.py data/processed/book.json

# Exercise generation
uv run src/exercise_generator.py data/processed/book_contexts.json

# LLM connection
uv run src/llm_client.py
```

## Known Limitations

1. **Single user** - No multi-user support yet
2. **In-memory sessions** - Conversations reset on server restart
3. **No persistence** - Progress not saved between sessions
4. **Sequential processing** - Books processed one at a time
5. **Limited formats** - Only PDF and EPUB supported
6. **English-focused** - Prompts optimized for English content

## Credits

Built with:
- Flask framework
- PyPDF2 & pdfplumber for document parsing
- EbookLib for EPUB support
- LLM Studio for local AI models
- Modern web standards (HTML5, CSS3, ES6)

## License

This project is provided as-is for educational purposes.

## Getting Started

See [QUICKSTART.md](QUICKSTART.md) for 5-minute setup guide!

---

**Transform any book into an interactive learning experience with AI-powered conversations!**
