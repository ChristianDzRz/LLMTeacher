import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Flask settings
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# LLM Studio settings
LLM_STUDIO_URL = os.getenv('LLM_STUDIO_URL', 'http://localhost:1234/v1')
LLM_MODEL = os.getenv('LLM_MODEL', 'local-model')

# File upload settings
UPLOAD_FOLDER = BASE_DIR / 'data' / 'books'
PROCESSED_FOLDER = BASE_DIR / 'data' / 'processed'
ALLOWED_EXTENSIONS = {'pdf', 'epub'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Data paths
USER_PROGRESS_FILE = BASE_DIR / 'data' / 'user_progress.json'

# Ensure directories exist
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)
