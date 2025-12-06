# Book Learning App

A conversational learning application that transforms books into structured learning plans with AI-powered tutoring.

## Features

- Upload PDF/EPUB books
- Automatic extraction of key learning topics
- Conversational AI tutor for each topic
- Exercise generation for knowledge reinforcement
- Progress tracking

## Quick Setup

1. Install dependencies:
```bash
uv sync
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your LLM Studio settings
```

3. Run the application:
```bash
uv run app.py
```

4. Open browser to `http://localhost:5000`

## Alternative Methods

**Using pip:**
```bash
pip install -r requirements.txt
python app.py
```

**Using convenience script (auto-detects uv/python):**
```bash
./run.sh
```

## Requirements

- Python 3.8+
- LLM Studio running locally (default: http://localhost:1234)

## Project Structure

- `app.py` - Main Flask application
- `config.py` - Configuration settings
- `src/` - Core functionality modules
- `templates/` - HTML templates
- `static/` - CSS/JS files
- `data/` - Book storage and processed data
