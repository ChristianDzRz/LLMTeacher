#!/usr/bin/env python3
"""
Test script to verify Book Learning App setup.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def test_imports():
    """Test that all required modules can be imported."""
    print_section("Testing Imports")

    modules = [
        ("Flask", "flask"),
        ("PyPDF2", "PyPDF2"),
        ("pdfplumber", "pdfplumber"),
        ("EbookLib", "ebooklib"),
        ("Requests", "requests"),
    ]

    all_ok = True

    for name, module in modules:
        try:
            __import__(module)
            print(f"✓ {name:20} imported successfully")
        except ImportError as e:
            print(f"✗ {name:20} FAILED: {e}")
            all_ok = False

    return all_ok


def test_directories():
    """Test that required directories exist."""
    print_section("Testing Directory Structure")

    base_dir = Path(__file__).parent

    dirs = [
        "data/books",
        "data/processed",
        "src",
        "templates",
        "static/css",
        "static/js",
    ]

    all_ok = True

    for dir_path in dirs:
        full_path = base_dir / dir_path
        if full_path.exists():
            print(f"✓ {dir_path:30} exists")
        else:
            print(f"✗ {dir_path:30} MISSING")
            all_ok = False

    return all_ok


def test_source_modules():
    """Test that source modules can be imported."""
    print_section("Testing Source Modules")

    modules = [
        "src.document_parser",
        "src.llm_client",
        "src.topic_extractor",
        "src.context_manager",
        "src.exercise_generator",
    ]

    all_ok = True

    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module:30} imported successfully")
        except Exception as e:
            print(f"✗ {module:30} FAILED: {e}")
            all_ok = False

    return all_ok


def test_llm_connection():
    """Test LLM Studio connection."""
    print_section("Testing LLM Studio Connection")

    try:
        from src.llm_client import LLMClient

        client = LLMClient()
        print(f"LLM Studio URL: {client.base_url}")
        print(f"Model: {client.model}")
        print("\nAttempting connection...")

        if client.test_connection():
            print("✓ LLM Studio connection successful!")

            # Try a simple prompt
            response = client.simple_prompt(
                "Say 'Hello from Book Learning App!'", max_tokens=50
            )
            print(f"\nTest response: {response[:100]}...")

            return True
        else:
            print("✗ LLM Studio connection failed!")
            print("\nTroubleshooting steps:")
            print("1. Make sure LLM Studio is running")
            print("2. Check that a model is loaded")
            print("3. Verify server is started (look for 'Server running' message)")
            print(f"4. Try accessing {client.base_url}/models in your browser")
            return False

    except Exception as e:
        print(f"✗ Error testing LLM connection: {e}")
        return False


def test_document_parser():
    """Test document parser with a sample."""
    print_section("Testing Document Parser")

    try:
        from src.document_parser import DocumentParser

        # Test statistics function
        test_text = "This is a test. " * 100
        stats = DocumentParser.get_text_statistics(test_text)

        print(f"✓ DocumentParser initialized")
        print(
            f"  Sample stats: {stats['word_count']} words, {stats['char_count']} chars"
        )

        return True
    except Exception as e:
        print(f"✗ Document parser test failed: {e}")
        return False


def test_config():
    """Test configuration."""
    print_section("Testing Configuration")

    try:
        import config

        print(f"✓ Configuration loaded")
        print(f"  Debug mode: {config.DEBUG}")
        print(f"  Upload folder: {config.UPLOAD_FOLDER}")
        print(f"  Processed folder: {config.PROCESSED_FOLDER}")
        print(f"  LLM Studio URL: {config.LLM_STUDIO_URL}")
        print(f"  Allowed extensions: {config.ALLOWED_EXTENSIONS}")

        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "+" * 60)
    print("  Book Learning App - Setup Test")
    print("+" * 60)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Directories", test_directories()))
    results.append(("Configuration", test_config()))
    results.append(("Source Modules", test_source_modules()))
    results.append(("Document Parser", test_document_parser()))
    results.append(("LLM Connection", test_llm_connection()))

    # Summary
    print_section("Test Summary")

    all_passed = all(result for _, result in results)

    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name:20} {status}")

    print("\n" + "-" * 60)

    if all_passed:
        print("✓ All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Run: python app.py")
        print("2. Open: http://localhost:5000")
        print("3. Upload a book and start learning!")
        return 0
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        print("\nCommon issues:")
        print("- Missing dependencies: pip install -r requirements.txt")
        print("- LLM Studio not running: Start LLM Studio and load a model")
        print("- Missing .env file: cp .env.example .env")
        return 1


if __name__ == "__main__":
    sys.exit(main())
