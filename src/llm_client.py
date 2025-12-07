"""
LLM Studio client for interacting with local language models.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

import requests

# Add parent directory to path for imports when running as standalone script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

import config


class LLMClient:
    """Client for communicating with LLM Studio API."""

    def __init__(self, base_url: str = None, model: str = None):
        """
        Initialize LLM client.

        Args:
            base_url: LLM Studio API URL (defaults to config)
            model: Model name to use (defaults to config)
        """
        self.base_url = base_url or config.LLM_STUDIO_URL
        self.model = model or config.LLM_MODEL
        self.chat_endpoint = f"{self.base_url}/chat/completions"

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
        timeout: int = 600,
    ) -> str:
        """
        Send chat completion request to LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            stream: Whether to stream the response
            timeout: Request timeout in seconds (default 600 = 10 minutes)

        Returns:
            Generated text response
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        try:
            print(
                f"Sending request to {self.chat_endpoint} with model {self.model} (timeout: {timeout}s)"
            )
            response = requests.post(self.chat_endpoint, json=payload, timeout=timeout)
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except requests.exceptions.Timeout as e:
            error_msg = f"LLM API request timed out after {timeout} seconds"
            print(error_msg)
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            # Print more details for debugging
            error_msg = f"LLM API request failed: {e}"
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_details = e.response.json()
                    error_msg += f"\nDetails: {error_details}"
                except:
                    error_msg += f"\nResponse: {e.response.text}"
            print(error_msg)
            raise Exception(error_msg)
        except (KeyError, IndexError) as e:
            error_msg = f"Invalid response format from LLM: {e}"
            print(error_msg)
            raise Exception(error_msg)

    def simple_prompt(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: int = 600,
    ) -> str:
        """
        Simple prompt completion (convenience method).

        Args:
            prompt: User prompt
            system_message: Optional system message
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds (default 600 = 10 minutes)

        Returns:
            Generated text response
        """
        messages = []

        if system_message:
            messages.append({"role": "system", "content": system_message})

        messages.append({"role": "user", "content": prompt})

        return self.chat(messages, temperature, max_tokens, timeout=timeout)

    def test_connection(self) -> bool:
        """
        Test if LLM Studio is accessible.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.simple_prompt(
                "Hello, respond with 'OK' if you can read this.", max_tokens=10
            )
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False


class ConversationManager:
    """Manage conversation history and context for study sessions."""

    def __init__(self, llm_client: LLMClient, system_prompt: str = None):
        """
        Initialize conversation manager.

        Args:
            llm_client: LLM client instance
            system_prompt: System prompt for the conversation
        """
        self.llm_client = llm_client
        self.messages = []

        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.messages.append({"role": role, "content": content})

    def send_user_message(
        self, message: str, temperature: float = 0.7, max_tokens: int = 2000
    ) -> str:
        """
        Send user message and get AI response.

        Args:
            message: User message
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            AI response
        """
        self.add_message("user", message)

        response = self.llm_client.chat(
            self.messages, temperature=temperature, max_tokens=max_tokens
        )

        self.add_message("assistant", response)

        return response

    def get_history(self) -> List[Dict[str, str]]:
        """Get full conversation history."""
        return self.messages.copy()

    def clear_history(self, keep_system_prompt: bool = True):
        """
        Clear conversation history.

        Args:
            keep_system_prompt: Whether to keep the system prompt
        """
        if (
            keep_system_prompt
            and self.messages
            and self.messages[0]["role"] == "system"
        ):
            system_msg = self.messages[0]
            self.messages = [system_msg]
        else:
            self.messages = []

    def get_message_count(self) -> int:
        """Get number of messages in conversation."""
        return len(self.messages)


class PromptTemplates:
    """Pre-defined prompt templates for different tasks."""

    @staticmethod
    def topic_extraction_prompt(book_content: str, book_title: str) -> str:
        """
        Generate prompt for extracting key learning topics from a book.

        Args:
            book_content: Full book text
            book_title: Title of the book

        Returns:
            Formatted prompt
        """
        return f"""You are an expert educator analyzing the book "{book_title}".

Your task is to create a comprehensive learning plan by identifying the key topics that a student should understand from this book.

Book content:
{book_content}

Please analyze this book and create a learning plan with 8-15 key topics. For each topic:
1. Provide a clear, concise title
2. Write a brief description (1-2 sentences) of what will be covered
3. Estimate the importance level (High/Medium/Low)

CRITICAL INSTRUCTIONS:
- You MUST respond with ONLY valid JSON
- NO explanations, NO extra text, NO markdown
- Start your response with [ and end with ]
- Do NOT add any text before or after the JSON

Format your response EXACTLY as this JSON array:
[
  {{
    "topic_number": 1,
    "title": "Topic Title",
    "description": "What this topic covers",
    "importance": "High"
  }},
  {{
    "topic_number": 2,
    "title": "Another Topic",
    "description": "Another description",
    "importance": "Medium"
  }}
]

Focus on topics that are:
- Essential for understanding the book's main concepts
- Build upon each other logically
- Comprehensive but not overwhelming

IMPORTANT: Return ONLY the JSON array. Start with [ and end with ]. No other text."""

    @staticmethod
    def tutoring_system_prompt(
        topic_title: str, topic_description: str, context: str
    ) -> str:
        """
        Generate system prompt for tutoring session.

        Args:
            topic_title: Title of the topic being studied
            topic_description: Description of the topic
            context: Relevant book content for this topic

        Returns:
            System prompt
        """
        return f"""You are an expert tutor helping a student learn about: {topic_title}

Topic description: {topic_description}

Relevant content from the book:
{context}

Your role:
- Explain concepts clearly and conversationally, as if talking to a curious student
- Break down complex ideas into understandable parts
- Use examples and analogies to clarify difficult concepts
- Ask questions to check understanding
- Identify and fill knowledge gaps
- Be encouraging and patient
- Build from fundamentals to advanced concepts
- Relate new information to what the student already knows

Guidelines:
- Keep explanations concise but thorough
- Use a friendly, approachable tone
- Encourage questions and curiosity
- Provide practical examples when possible
- Don't just recite the book - teach and explain

Begin by introducing the topic and asking what the student already knows about it."""

    @staticmethod
    def exercise_generation_prompt(topic_title: str, context: str) -> str:
        """
        Generate prompt for creating exercises.

        Args:
            topic_title: Title of the topic
            context: Relevant book content

        Returns:
            Formatted prompt
        """
        return f"""Based on the topic "{topic_title}" and the following content, create 5 exercises to help solidify understanding.

Content:
{context}

Create a mix of:
- Conceptual questions (test understanding of key ideas)
- Application problems (apply concepts to scenarios)
- Practical exercises (hands-on activities if applicable)

Format as JSON:
[
  {{
    "exercise_number": 1,
    "type": "conceptual",
    "question": "Question or exercise prompt",
    "hint": "Optional hint to help answer"
  }},
  ...
]

Make exercises challenging but achievable. Focus on reinforcing the most important concepts.

Respond ONLY with the JSON array."""


if __name__ == "__main__":
    # Simple connection test
    print("Testing LLM Studio connection...")

    client = LLMClient()

    if client.test_connection():
        print("✓ Connection successful!")

        # Test simple prompt
        response = client.simple_prompt("What is 2+2? Answer briefly.", max_tokens=50)
        print(f"\nTest response: {response}")
    else:
        print("✗ Connection failed!")
        print(f"Make sure LLM Studio is running at {client.base_url}")
