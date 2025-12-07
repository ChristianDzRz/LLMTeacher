import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Flask settings
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
DEBUG = os.getenv("DEBUG", "True") == "True"

# Ollama settings
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2-gpu")

# LM Studio settings
LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "openai/gpt-oss-20b")

# Processing model settings (for book processing)
# Can be "ollama" or "lmstudio"
PROCESSING_PROVIDER = os.getenv("PROCESSING_PROVIDER", "ollama")
PROCESSING_MODEL = os.getenv(
    "PROCESSING_MODEL",
    OLLAMA_MODEL if PROCESSING_PROVIDER == "ollama" else LM_STUDIO_MODEL,
)

# Legacy compatibility - keep for now
LLM_STUDIO_URL = OLLAMA_URL
LLM_MODEL = OLLAMA_MODEL

# Chat API settings - default to Ollama if LM Studio not available
CHAT_API_URL = os.getenv("CHAT_API_URL", OLLAMA_URL)
CHAT_MODEL = os.getenv("CHAT_MODEL", OLLAMA_MODEL)

# File upload settings
UPLOAD_FOLDER = BASE_DIR / "data" / "books"
PROCESSED_FOLDER = BASE_DIR / "data" / "processed"
ALLOWED_EXTENSIONS = {"pdf", "epub"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Data paths
USER_PROGRESS_FILE = BASE_DIR / "data" / "user_progress.json"

# Ensure directories exist
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)
