import json
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request, session
from werkzeug.utils import secure_filename

import config
from src.chapter_processor import ChapterProcessor
from src.context_manager import ContextManager
from src.document_parser import DocumentParser
from src.exercise_generator import ExerciseGenerator
from src.llm_client import ConversationManager, LLMClient, PromptTemplates
from src.topic_extractor import TopicExtractor

app = Flask(__name__)
app.config.from_object(config)

# Initialize components
# Ollama client for book processing
llm_client = LLMClient()
topic_extractor = TopicExtractor(llm_client)
context_manager = ContextManager(llm_client)
exercise_generator = ExerciseGenerator(llm_client)

# OpenAI/LM Studio client for chat conversations
chat_client = LLMClient(base_url=config.CHAT_API_URL, model=config.CHAT_MODEL)

# Store active conversations in memory (could be moved to database later)
conversations = {}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS
    )


def get_current_book_path():
    """Get path to currently processed book data (structure file)."""
    # For simplicity, we'll use the most recent processed book
    processed_dir = Path(config.PROCESSED_FOLDER)
    if not processed_dir.exists():
        return None

    # Look for structure files in book folders
    structure_files = []
    for book_folder in processed_dir.iterdir():
        if book_folder.is_dir():
            structure_file = book_folder / "structure.json"
            if structure_file.exists():
                structure_files.append(structure_file)

    if not structure_files:
        return None

    # Return most recent
    return max(structure_files, key=lambda p: p.stat().st_mtime)


def load_book_data(folder_name=None):
    """
    Load processed book structure data.

    Args:
        folder_name: Book folder name (e.g., "Title - Author (Year)")
                    If None, loads most recent book
    """
    if folder_name:
        # Load specific book by folder name
        book_folder = Path(config.PROCESSED_FOLDER) / folder_name
        structure_path = book_folder / "structure.json"
        if not structure_path.exists():
            return None
    else:
        # Load most recent book
        structure_path = get_current_book_path()
        if not structure_path:
            return None

    with open(structure_path, "r", encoding="utf-8") as f:
        book_structure = json.load(f)

    return book_structure


def load_chapter_data(book_folder_name, chapter_number):
    """
    Load individual chapter data.

    Args:
        book_folder_name: Book folder name (e.g., "Title - Author (Year)")
        chapter_number: Chapter number to load
    """
    chapter_path = (
        Path(config.PROCESSED_FOLDER)
        / book_folder_name
        / f"chapter_{chapter_number}.json"
    )

    if not chapter_path.exists():
        return None

    with open(chapter_path, "r", encoding="utf-8") as f:
        chapter_data = json.load(f)

    return chapter_data


@app.route("/")
def index():
    """Main page - upload book or view existing learning plan"""
    return render_template("upload.html")


import threading


def process_book_background(
    filepath, toc_text, processing_provider=None, processing_model=None
):
    """Process book in background thread using chapter-based processing."""
    try:
        print(f"Background processing started for: {filepath}")

        # Determine which API to use based on provider
        if processing_provider == "lmstudio":
            # LM Studio
            model = processing_model or config.LM_STUDIO_MODEL
            print(f"Using LM Studio model: {model}")
            custom_llm_client = LLMClient(base_url=config.LM_STUDIO_URL, model=model)
            chapter_processor = ChapterProcessor(custom_llm_client)
        elif processing_provider == "ollama":
            # Ollama
            model = processing_model or config.OLLAMA_MODEL
            print(f"Using Ollama model: {model}")
            custom_llm_client = LLMClient(base_url=config.OLLAMA_URL, model=model)
            chapter_processor = ChapterProcessor(custom_llm_client)
        else:
            # Default to config settings
            print(f"Using default provider: {config.PROCESSING_PROVIDER}")
            if config.PROCESSING_PROVIDER == "lmstudio":
                custom_llm_client = LLMClient(
                    base_url=config.LM_STUDIO_URL, model=config.PROCESSING_MODEL
                )
                chapter_processor = ChapterProcessor(custom_llm_client)
            else:
                chapter_processor = ChapterProcessor(llm_client)

        # Process book chapter by chapter
        result = chapter_processor.process_book(filepath, toc_text=toc_text)

        print("Background processing complete!")
        print(
            f"Created structure file and {len(result.get('chapters', []))} chapter files"
        )

    except Exception as e:
        print(f"Background processing error: {e}")
        import traceback

        traceback.print_exc()


@app.route("/upload", methods=["POST"])
def upload_book():
    """Handle book upload and trigger processing"""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(config.UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Get optional TOC from form
        toc_text = request.form.get("toc", "").strip()

        # Get processing provider and model from form
        processing_provider = request.form.get("processing_provider", "").strip()
        processing_model = request.form.get("processing_model", "").strip()

        print(f"Processing book: {filename}")
        if toc_text:
            print(f"Using user-provided TOC ({len(toc_text)} chars)")
        if processing_provider:
            print(f"Using processing provider: {processing_provider}")
        if processing_model:
            print(f"Using processing model: {processing_model}")

        # Initialize progress file immediately to avoid showing old book
        import tempfile

        progress_file = Path(tempfile.gettempdir()) / "book_processing_progress.json"
        try:
            with open(progress_file, "w") as f:
                json.dump(
                    {
                        "progress": 0,
                        "current": 0,
                        "total": 1,
                        "message": f"Starting to process {filename}...",
                        "book_folder": None,  # Will be set once book folder is created
                        "upload_filename": filename,
                    },
                    f,
                )
            print(f"Initialized progress file for {filename}")
        except Exception as e:
            print(f"Warning: Could not initialize progress file: {e}")

        # Start processing in background thread
        thread = threading.Thread(
            target=process_book_background,
            args=(filepath, toc_text, processing_provider, processing_model),
        )
        thread.daemon = True
        thread.start()

        # Return immediately so frontend can start monitoring
        return jsonify(
            {"success": True, "filename": filename, "message": "Processing started"}
        )

    return jsonify({"error": "Invalid file type"}), 400


@app.route("/learning-plan")
def learning_plan():
    """Display the generated learning plan (chapters)"""
    # Check if a specific book is requested
    book_filename = request.args.get("book")
    book_structure = load_book_data(book_filename)

    if not book_structure:
        return render_template("learning_plan.html", book_info=None, chapters=None)

    return render_template(
        "learning_plan.html",
        book_info=book_structure["book_info"],
        chapters=book_structure.get("overview", {}).get("chapters", []),
        book_summary=book_structure.get("overview", {}).get("book_summary", ""),
        current_book=book_filename,
    )


@app.route("/study/chapter/<int:chapter_number>/topic/<int:topic_number>")
def study_topic(chapter_number, topic_number):
    """Study interface for a specific topic within a chapter"""
    # Get book filename from query parameter
    book_filename = request.args.get("book")

    print(
        f"[DEBUG] Study route called: chapter={chapter_number}, topic={topic_number}, book={book_filename}"
    )

    # Load chapter data
    chapter_data = load_chapter_data(book_filename, chapter_number)

    if not chapter_data:
        print(f"[DEBUG] Chapter {chapter_number} not found for book {book_filename}")
        return "Chapter not found", 404

    # Find the topic within the chapter
    topic = None
    topic_index = None
    topics = chapter_data.get("topics", [])
    print(f"[DEBUG] Chapter has {len(topics)} topics")

    # If no topics exist, create a default one
    if not topics:
        print(f"[DEBUG] No topics found, creating default topic")
        topics = [
            {
                "topic_number": 1,
                "title": chapter_data.get("title", f"Chapter {chapter_number}"),
                "description": f"Study the content of this chapter",
                "key_points": ["Review the chapter content"],
                "importance": "High",
                "suggested_search_queries": [],
            }
        ]
        chapter_data["topics"] = topics

    for i, t in enumerate(topics):
        if t["topic_number"] == topic_number:
            topic = t
            topic_index = i
            break

    if not topic:
        print(
            f"[DEBUG] Topic {topic_number} not found in topics: {[t.get('topic_number') for t in topics]}"
        )
        return "Topic not found", 404

    # Determine navigation
    has_next_topic = topic_index < len(topics) - 1
    has_prev_topic = topic_index > 0

    next_topic_num = topics[topic_index + 1]["topic_number"] if has_next_topic else None
    prev_topic_num = topics[topic_index - 1]["topic_number"] if has_prev_topic else None

    # Check if there's a next chapter (load book structure)
    book_structure = load_book_data(book_filename)
    has_next_chapter = False
    next_chapter_num = None

    if book_structure and not has_next_topic:
        total_chapters = book_structure.get("book_info", {}).get("chapter_count", 0)
        if chapter_number < total_chapters:
            has_next_chapter = True
            next_chapter_num = chapter_number + 1

    # Initialize conversation for this topic if not exists
    # Use book and chapter-specific conversation key
    conv_key = f"ch{chapter_number}_topic_{topic_number}_{book_filename if book_filename else 'default'}"
    if conv_key not in conversations:
        # Create context from chapter content preview and topic info
        context = chapter_data.get("content_preview", "")

        # Add key points to context
        key_points = "\n".join([f"- {point}" for point in topic.get("key_points", [])])

        # Add suggested search queries
        search_queries = topic.get("suggested_search_queries", [])
        search_context = ""
        if search_queries:
            search_context = f"\n\nSuggested topics to explore:\n" + "\n".join(
                [f"- {q}" for q in search_queries]
            )

        full_context = f"{context}\n\nKey Points:\n{key_points}{search_context}"

        # Create system prompt
        system_prompt = PromptTemplates.tutoring_system_prompt(
            topic["title"],
            topic.get("description", ""),
            full_context[:4000],  # Limit context size
        )

        conversations[conv_key] = ConversationManager(chat_client, system_prompt)

    return render_template(
        "study.html",
        chapter_number=chapter_number,
        topic_number=topic_number,
        topic=topic,
        book_filename=book_filename,
        chapter_title=chapter_data.get("title", f"Chapter {chapter_number}"),
        has_next_topic=has_next_topic,
        has_prev_topic=has_prev_topic,
        next_topic_num=next_topic_num,
        prev_topic_num=prev_topic_num,
        has_next_chapter=has_next_chapter,
        next_chapter_num=next_chapter_num,
    )


@app.route("/api/chat", methods=["POST"])
def chat():
    """Handle chat messages during study session"""
    data = request.json
    chapter_number = data.get("chapter_number")
    topic_number = data.get("topic_number")
    message = data.get("message")
    selected_model = data.get("model", config.CHAT_MODEL)
    book_filename = data.get("book_filename")

    if not message:
        return jsonify({"error": "No message provided"}), 400

    conv_key = f"ch{chapter_number}_topic_{topic_number}_{book_filename if book_filename else 'default'}"

    # If conversation doesn't exist or model changed, reinitialize with new model
    if conv_key not in conversations or (
        hasattr(conversations[conv_key], "_model")
        and conversations[conv_key]._model != selected_model
    ):
        # Load chapter data
        chapter_data = load_chapter_data(book_filename, chapter_number)
        if not chapter_data:
            return jsonify({"error": "Chapter not found"}), 404

        # Find the topic
        topic = None
        for t in chapter_data.get("topics", []):
            if t["topic_number"] == topic_number:
                topic = t
                break

        if topic:
            # Create context from chapter content and topic info
            context = chapter_data.get("content_preview", "")
            key_points = "\n".join(
                [f"- {point}" for point in topic.get("key_points", [])]
            )

            search_queries = topic.get("suggested_search_queries", [])
            search_context = ""
            if search_queries:
                search_context = f"\n\nSuggested topics to explore:\n" + "\n".join(
                    [f"- {q}" for q in search_queries]
                )

            full_context = f"{context}\n\nKey Points:\n{key_points}{search_context}"

            # Create system prompt
            system_prompt = PromptTemplates.tutoring_system_prompt(
                topic["title"],
                topic.get("description", ""),
                full_context[:4000],
            )

            # Create new conversation with selected model
            custom_chat_client = LLMClient(
                base_url=config.CHAT_API_URL, model=selected_model
            )
            custom_chat_client._model = selected_model  # Store for comparison
            conversations[conv_key] = ConversationManager(
                custom_chat_client, system_prompt
            )
            conversations[conv_key]._model = selected_model

    try:
        # Get response from LLM
        response = conversations[conv_key].send_user_message(message)

        return jsonify({"response": response})
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({"error": "Failed to get response"}), 500


@app.route("/api/generate-exercises", methods=["POST"])
def generate_exercises_route():
    """Generate exercises for a topic in a chapter"""
    data = request.json
    chapter_number = data.get("chapter_number")
    topic_number = data.get("topic_number")
    book_filename = data.get("book_filename")
    model = data.get("model")  # Get the selected model

    if not chapter_number or not topic_number:
        return jsonify({"error": "Missing chapter_number or topic_number"}), 400

    # Load chapter data
    chapter_data = load_chapter_data(book_filename, chapter_number)

    if not chapter_data:
        return jsonify({"error": "Chapter not found"}), 404

    # Find the topic within the chapter
    topic = None
    for t in chapter_data.get("topics", []):
        if t["topic_number"] == topic_number:
            topic = t
            break

    if not topic:
        return jsonify({"error": "Topic not found"}), 404

    # Use chapter content preview as context
    context = chapter_data.get("content_preview", "")

    # Add key points to context
    key_points = topic.get("key_points", [])
    if key_points:
        context += "\n\nKey Points:\n" + "\n".join(
            [f"- {point}" for point in key_points]
        )

    if not context:
        return jsonify({"error": "No context available for this topic"}), 404

    try:
        # Create custom LLM client with selected model if specified
        if model:
            print(f"Using model for exercises: {model}")
            custom_llm_client = LLMClient(base_url=config.CHAT_API_URL, model=model)
            custom_exercise_generator = ExerciseGenerator(custom_llm_client)
        else:
            custom_exercise_generator = exercise_generator

        # Generate exercises (increased to 10)
        print(f"Generating exercises for topic: {topic.get('title', 'Unknown')}")
        exercises = custom_exercise_generator.generate_exercises(
            topic, context, num_exercises=10
        )
        print(f"Successfully generated {len(exercises)} exercises")

        return jsonify({"exercises": exercises})
    except Exception as e:
        print(f"Exercise generation error: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": f"Failed to generate exercises: {str(e)}"}), 500


@app.route("/api/validate-answer", methods=["POST"])
def validate_answer():
    """Validate a user's exercise answer"""
    data = request.get_json()

    if (
        not data
        or "chapter_number" not in data
        or "topic_number" not in data
        or "exercise" not in data
        or "user_answer" not in data
    ):
        return jsonify({"error": "Missing required fields"}), 400

    chapter_number = data.get("chapter_number")
    topic_number = data.get("topic_number")
    exercise = data.get("exercise")
    user_answer = data.get("user_answer", "")
    book_filename = data.get("book_filename")
    model = data.get("model")  # Get the selected model

    # Load chapter data
    chapter_data = load_chapter_data(book_filename, chapter_number)
    if not chapter_data:
        return jsonify({"error": "Chapter not found"}), 404

    # Find the topic
    topic = None
    for t in chapter_data.get("topics", []):
        if t["topic_number"] == topic_number:
            topic = t
            break

    if not topic:
        return jsonify({"error": "Topic not found"}), 404

    # Get context for validation
    context = chapter_data.get("content_preview", "")
    key_points = topic.get("key_points", [])
    if key_points:
        context += "\n\nKey Points:\n" + "\n".join(
            [f"- {point}" for point in key_points]
        )

    if not context:
        return jsonify({"error": "No context available"}), 404

    try:
        # Create custom LLM client with selected model if specified
        if model:
            print(f"Using model for answer validation: {model}")
            custom_llm_client = LLMClient(base_url=config.CHAT_API_URL, model=model)
            custom_exercise_generator = ExerciseGenerator(custom_llm_client)
        else:
            custom_exercise_generator = exercise_generator

        # Validate the answer
        validation = custom_exercise_generator.validate_answer(
            exercise, user_answer, context
        )
        return jsonify(validation)
    except Exception as e:
        print(f"Answer validation error: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": "Failed to validate answer"}), 500


@app.route("/api/clear-conversation/<int:topic_id>", methods=["POST"])
def clear_conversation(topic_id):
    """Clear conversation history for a topic"""
    conv_key = f"topic_{topic_id}"

    if conv_key in conversations:
        conversations[conv_key].clear_history(keep_system_prompt=True)
        return jsonify({"success": True})

    return jsonify({"error": "Conversation not found"}), 404


@app.route("/health")
def health():
    """Health check endpoint"""
    llm_status = llm_client.test_connection()

    return jsonify(
        {
            "status": "ok",
            "llm_connected": llm_status,
            "books_processed": len(list(Path(config.PROCESSED_FOLDER).glob("*.json"))),
        }
    )


@app.route("/api/available-models")
def get_available_models():
    """Get available models from both Ollama and LM Studio."""
    import requests

    models = {
        "ollama": [],
        "lm_studio": [],
        "ollama_available": False,
        "lm_studio_available": False,
    }

    # Try to fetch Ollama models
    try:
        response = requests.get(
            f"{config.OLLAMA_URL.replace('/v1', '')}/api/tags", timeout=2
        )
        if response.status_code == 200:
            data = response.json()
            models["ollama"] = [
                {
                    "name": model["name"],
                    "size": model.get("size", 0),
                    "parameter_size": model.get("details", {}).get(
                        "parameter_size", ""
                    ),
                }
                for model in data.get("models", [])
            ]
            models["ollama_available"] = True
    except Exception as e:
        print(f"Could not fetch Ollama models: {e}")

    # Try to fetch LM Studio models
    try:
        response = requests.get(f"{config.LM_STUDIO_URL}/models", timeout=2)
        if response.status_code == 200:
            data = response.json()
            models["lm_studio"] = [
                {"id": model["id"], "name": model.get("id", model.get("name", ""))}
                for model in data.get("data", [])
            ]
            models["lm_studio_available"] = True
    except Exception as e:
        print(f"Could not fetch LM Studio models: {e}")

    return jsonify(models)


@app.route("/api/chapter/<int:chapter_number>")
def get_chapter_topics(chapter_number):
    """Get topics for a specific chapter."""
    book_filename = request.args.get("book")

    if not book_filename:
        # Try to get most recent book
        book_path = get_current_book_path()
        if book_path:
            # book_path is path to structure.json, get parent folder name
            book_filename = book_path.parent.name

    if not book_filename:
        return jsonify({"error": "No book specified"}), 400

    chapter_data = load_chapter_data(book_filename, chapter_number)

    if not chapter_data:
        return jsonify({"error": "Chapter not found"}), 404

    return jsonify(chapter_data)


@app.route("/api/processed-books")
def get_processed_books():
    """Get list of previously processed books."""
    processed_dir = Path(config.PROCESSED_FOLDER)
    books = []

    if processed_dir.exists():
        # Get structure files from book folders
        for book_folder in processed_dir.iterdir():
            if not book_folder.is_dir():
                continue

            structure_file = book_folder / "structure.json"
            if not structure_file.exists():
                continue

            try:
                with open(structure_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    book_info = data.get("book_info", {})
                    books.append(
                        {
                            "folder_name": book_folder.name,
                            "title": book_info.get("title", book_folder.name),
                            "author": book_info.get("metadata", {}).get("author", ""),
                            "word_count": book_info.get("word_count", 0),
                            "chapter_count": book_info.get("chapter_count", 0),
                            "processed_date": structure_file.stat().st_mtime,
                        }
                    )
            except Exception as e:
                print(f"Error reading {structure_file}: {e}")

    # Sort by most recently processed
    books.sort(key=lambda x: x["processed_date"], reverse=True)
    return jsonify({"books": books})


@app.route("/api/load-book/<path:filename>")
def load_book(filename):
    """Load a previously processed book."""
    processed_dir = Path(config.PROCESSED_FOLDER)
    book_file = processed_dir / filename

    if not book_file.exists():
        return jsonify({"error": "Book not found"}), 404

    # Just return success - the learning plan page will load the book
    return jsonify({"success": True, "filename": filename})


@app.route("/api/processing-status")
def processing_status():
    """Get current processing status."""
    import tempfile
    from pathlib import Path

    # Try to read progress from temp file
    progress_file = Path(tempfile.gettempdir()) / "book_processing_progress.json"
    progress = 0
    message = ""
    book_folder = None
    upload_filename = None

    print(f"[DEBUG] Checking progress file: {progress_file}")
    print(f"[DEBUG] Progress file exists: {progress_file.exists()}")

    if progress_file.exists():
        try:
            with open(progress_file, "r") as f:
                progress_data = json.load(f)
                progress = progress_data.get("progress", 0)
                message = progress_data.get("message", "")
                book_folder = progress_data.get("book_folder", None)
                upload_filename = progress_data.get("upload_filename", None)
                print(f"[DEBUG] Progress data: {progress_data}")
                print(f"[DEBUG] Book folder from progress: {book_folder}")
                print(f"[DEBUG] Upload filename: {upload_filename}")
        except Exception as e:
            print(f"[DEBUG] Error reading progress file: {e}")
            pass

    # If we have progress, we're processing
    if progress >= 0 and progress < 100:
        print(
            f"[DEBUG] Status: processing, folder: {book_folder}, upload: {upload_filename}"
        )
        return jsonify(
            {
                "status": "processing",
                "progress": progress,
                "message": message,
                "folder": book_folder,
                "upload_filename": upload_filename,
            }
        )

    # Check if processing is complete (progress == 100 and we have a book folder)
    if progress >= 100 and book_folder:
        # Verify the book folder exists
        book_path = Path(config.PROCESSED_FOLDER) / book_folder / "structure.json"
        print(f"[DEBUG] Checking complete book path: {book_path}")
        print(f"[DEBUG] Book path exists: {book_path.exists()}")
        if book_path.exists():
            print(f"[DEBUG] Status: complete, folder: {book_folder}")
            return jsonify(
                {"status": "complete", "progress": 100, "folder": book_folder}
            )

    # Fallback: Check for most recent completed book
    print(f"[DEBUG] Falling back to get_current_book_path()")
    book_path = get_current_book_path()
    if book_path and book_path.exists():
        fallback_folder = book_path.parent.name
        print(f"[DEBUG] Fallback folder: {fallback_folder}")
        # Book processing is complete
        return jsonify(
            {"status": "complete", "progress": 100, "folder": fallback_folder}
        )

    # If we have progress file but no book path yet, still return processing
    if progress > 0:
        return jsonify(
            {
                "status": "processing",
                "progress": progress,
                "message": message,
            }
        )

    # No processing
    return jsonify({"status": "idle", "progress": 0})


if __name__ == "__main__":
    app.run(debug=config.DEBUG)
