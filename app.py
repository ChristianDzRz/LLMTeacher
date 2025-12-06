import json
import os
from pathlib import Path

import config
from flask import Flask, jsonify, render_template, request, session
from src.context_manager import ContextManager
from src.document_parser import DocumentParser
from src.exercise_generator import ExerciseGenerator
from src.llm_client import ConversationManager, LLMClient, PromptTemplates
from src.topic_extractor import TopicExtractor
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(config)

# Initialize components
llm_client = LLMClient()
topic_extractor = TopicExtractor(llm_client)
context_manager = ContextManager(llm_client)
exercise_generator = ExerciseGenerator(llm_client)

# Store active conversations in memory (could be moved to database later)
conversations = {}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS
    )


def get_current_book_path():
    """Get path to currently processed book data."""
    # For simplicity, we'll use the most recent processed book
    processed_dir = Path(config.PROCESSED_FOLDER)
    if not processed_dir.exists():
        return None

    json_files = list(processed_dir.glob("*.json"))
    # Exclude _contexts.json files
    json_files = [f for f in json_files if not f.name.endswith("_contexts.json")]

    if not json_files:
        return None

    # Return most recent
    return max(json_files, key=lambda p: p.stat().st_mtime)


def load_book_data():
    """Load processed book data and contexts."""
    book_path = get_current_book_path()
    if not book_path:
        return None

    with open(book_path, "r", encoding="utf-8") as f:
        book_data = json.load(f)

    # Try to load contexts
    contexts_path = book_path.parent / f"{book_path.stem}_contexts.json"
    if contexts_path.exists():
        with open(contexts_path, "r", encoding="utf-8") as f:
            contexts = json.load(f)
        book_data["contexts"] = contexts
    else:
        book_data["contexts"] = {}

    return book_data


@app.route("/")
def index():
    """Main page - upload book or view existing learning plan"""
    return render_template("upload.html")


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

        try:
            # Process the book
            print(f"Processing book: {filename}")
            result = topic_extractor.process_book(filepath)

            # Extract contexts for topics (use keyword method for speed)
            print("Extracting topic contexts...")
            contexts = context_manager.build_topic_contexts(
                result["topics"],
                result["content"],
                use_llm=False,  # Use keyword method for faster processing
            )

            # Save contexts
            book_path = get_current_book_path()
            if book_path:
                contexts_path = book_path.parent / f"{book_path.stem}_contexts.json"
                with open(contexts_path, "w", encoding="utf-8") as f:
                    json.dump(contexts, f, indent=2, ensure_ascii=False)

            return jsonify(
                {
                    "success": True,
                    "filename": filename,
                    "topics_count": len(result["topics"]),
                }
            )

        except Exception as e:
            print(f"Error processing book: {e}")
            return jsonify({"error": f"Processing failed: {str(e)}"}), 500

    return jsonify({"error": "Invalid file type"}), 400


@app.route("/learning-plan")
def learning_plan():
    """Display the generated learning plan (topics)"""
    book_data = load_book_data()

    if not book_data:
        return render_template("learning_plan.html", book_info=None, topics=None)

    return render_template(
        "learning_plan.html",
        book_info=book_data["book_info"],
        topics=book_data["topics"],
    )


@app.route("/study/<int:topic_id>")
def study_topic(topic_id):
    """Study interface for a specific topic"""
    book_data = load_book_data()

    if not book_data:
        return "No book loaded", 404

    # Find the topic
    topic = None
    for t in book_data["topics"]:
        if t["topic_number"] == topic_id:
            topic = t
            break

    if not topic:
        return "Topic not found", 404

    # Initialize conversation for this topic if not exists
    conv_key = f"topic_{topic_id}"
    if conv_key not in conversations:
        # Get context for this topic
        context = book_data["contexts"].get(str(topic_id), {}).get("context", "")

        # Create system prompt
        system_prompt = PromptTemplates.tutoring_system_prompt(
            topic["title"],
            topic.get("description", ""),
            context[:4000],  # Limit context size
        )

        conversations[conv_key] = ConversationManager(llm_client, system_prompt)

    return render_template("study.html", topic_id=topic_id, topic=topic)


@app.route("/api/chat", methods=["POST"])
def chat():
    """Handle chat messages during study session"""
    data = request.json
    topic_id = data.get("topic_id")
    message = data.get("message")

    if not message:
        return jsonify({"error": "No message provided"}), 400

    conv_key = f"topic_{topic_id}"

    if conv_key not in conversations:
        return jsonify({"error": "Conversation not initialized"}), 400

    try:
        # Get response from LLM
        response = conversations[conv_key].send_user_message(message)

        return jsonify({"response": response})
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({"error": "Failed to get response"}), 500


@app.route("/api/generate-exercises/<int:topic_id>", methods=["POST"])
def generate_exercises_route(topic_id):
    """Generate exercises for a topic"""
    book_data = load_book_data()

    if not book_data:
        return jsonify({"error": "No book loaded"}), 404

    # Find the topic
    topic = None
    for t in book_data["topics"]:
        if t["topic_number"] == topic_id:
            topic = t
            break

    if not topic:
        return jsonify({"error": "Topic not found"}), 404

    # Get context
    context = book_data["contexts"].get(str(topic_id), {}).get("context", "")

    if not context:
        return jsonify({"error": "No context available for this topic"}), 404

    try:
        # Generate exercises
        exercises = exercise_generator.generate_exercises(
            topic, context, num_exercises=5
        )

        return jsonify({"exercises": exercises})
    except Exception as e:
        print(f"Exercise generation error: {e}")
        return jsonify({"error": "Failed to generate exercises"}), 500


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


if __name__ == "__main__":
    app.run(debug=config.DEBUG)
