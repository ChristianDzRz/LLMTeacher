"""
Exercise generator for creating practice problems from book content.
"""

import json
import re
from typing import Dict, List

from src.llm_client import LLMClient, PromptTemplates


class ExerciseGenerator:
    """Generate exercises to reinforce learning."""

    def __init__(self, llm_client: LLMClient = None):
        """
        Initialize exercise generator.

        Args:
            llm_client: LLM client instance (creates new one if not provided)
        """
        self.llm_client = llm_client or LLMClient()

    def generate_exercises(
        self,
        topic: Dict,
        context: str,
        num_exercises: int = 5,
        difficulty: str = "mixed",
    ) -> List[Dict]:
        """
        Generate exercises for a specific topic.

        Args:
            topic: Topic dictionary with 'title' and 'description'
            context: Relevant book content for this topic
            num_exercises: Number of exercises to generate
            difficulty: "easy", "medium", "hard", or "mixed"

        Returns:
            List of exercise dictionaries:
            [
                {
                    "exercise_number": 1,
                    "type": "conceptual",
                    "question": "Question text",
                    "hint": "Optional hint"
                },
                ...
            ]
        """
        prompt = self._create_exercise_prompt(topic, context, num_exercises, difficulty)

        print(f"Generating {num_exercises} exercises for topic: {topic['title']}")

        # Use longer timeout for exercise generation (especially for 10+ exercises)
        timeout = 600  # 10 minutes
        response = self.llm_client.simple_prompt(
            prompt, temperature=0.7, max_tokens=6000, timeout=timeout
        )

        exercises = self._parse_exercises_response(response)

        print(f"Generated {len(exercises)} exercises")

        return exercises

    def _create_exercise_prompt(
        self, topic: Dict, context: str, num_exercises: int, difficulty: str
    ) -> str:
        """Create prompt for exercise generation."""
        topic_title = topic["title"]
        topic_desc = topic.get("description", "")

        difficulty_guidance = {
            "easy": "Focus on basic recall and simple understanding questions.",
            "medium": "Include application and analysis questions.",
            "hard": "Create challenging problems requiring synthesis and evaluation.",
            "mixed": "Mix of easy, medium, and hard exercises.",
        }

        guidance = difficulty_guidance.get(difficulty, difficulty_guidance["mixed"])

        return f"""Based on the topic "{topic_title}" and the following content, create {num_exercises} exercises to help students solidify their understanding.

Topic Description: {topic_desc}

Content:
{context}

Create exercises with these types:
- Conceptual: Test understanding of key ideas and concepts
- Application: Apply concepts to new scenarios or problems
- Practical: Hands-on activities or exercises (if applicable)
- Analysis: Analyze, compare, or evaluate concepts

{guidance}

Format as JSON:
[
  {{
    "exercise_number": 1,
    "type": "conceptual",
    "difficulty": "easy",
    "question": "Clear, specific question or exercise prompt",
    "hint": "Optional hint to guide the student (can be empty string)"
  }},
  ...
]

Guidelines:
- Make questions specific and clear
- Ensure exercises test different aspects of the topic
- Include a variety of exercise types
- Questions should be challenging but achievable
- Focus on the most important concepts from the content

Respond ONLY with the JSON array."""

    @staticmethod
    def _parse_exercises_response(response: str) -> List[Dict]:
        """
        Parse LLM response containing exercises JSON.

        Args:
            response: LLM response (should contain JSON array)

        Returns:
            List of exercise dictionaries
        """
        # Debug logging
        print(f"\n{'=' * 60}")
        print("LLM Response for exercises:")
        print(f"{'=' * 60}")
        print(response[:500] if len(response) > 500 else response)
        if len(response) > 500:
            print(f"... (truncated, total length: {len(response)} chars)")
        print(f"{'=' * 60}\n")

        exercises = None

        # Strategy 1: Find JSON array with objects
        json_match = re.search(r"\[\s*\{.*\}\s*\]", response, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(0)
                # Clean up common issues
                json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
                exercises = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON (strategy 1): {e}")

        # Strategy 2: Try to find JSON in code blocks
        if not exercises:
            code_block_match = re.search(
                r"```(?:json)?\s*(\[.*?\])\s*```", response, re.DOTALL
            )
            if code_block_match:
                try:
                    json_str = code_block_match.group(1)
                    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
                    exercises = json.loads(json_str)
                    print("Successfully parsed JSON from code block")
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON (strategy 2): {e}")

        # Strategy 3: Strip everything except JSON array
        if not exercises:
            try:
                # Remove markdown, extra text, etc.
                cleaned = re.sub(r"^[^\[]*", "", response)  # Remove before first [
                cleaned = re.sub(r"[^\]]*$", "", cleaned)  # Remove after last ]
                json_str = re.sub(r",\s*([}\]])", r"\1", cleaned)
                exercises = json.loads(json_str)
                print("Successfully parsed JSON (strategy 3)")
            except (json.JSONDecodeError, Exception) as e:
                print(f"Failed to parse JSON (strategy 3): {e}")

        # Strategy 4: Just try to parse the whole response as-is
        if not exercises:
            try:
                json_str = response.strip()
                json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
                exercises = json.loads(json_str)
                print("Successfully parsed JSON (strategy 4 - raw)")
            except (json.JSONDecodeError, Exception) as e:
                print(f"Failed to parse JSON (strategy 4): {e}")

        if not exercises:
            # If all parsing fails, print full response and raise error
            print("\n" + "=" * 60)
            print("FULL LLM RESPONSE (parsing failed):")
            print("=" * 60)
            print(response)
            print("=" * 60 + "\n")
            raise ValueError(
                f"Failed to parse exercises JSON. Response length: {len(response)} chars. Check logs for full response."
            )

        # Validate it's a list
        if not isinstance(exercises, list):
            raise ValueError(f"Response is not a list, got: {type(exercises)}")

        # Validate and normalize structure
        for i, ex in enumerate(exercises, 1):
            if "question" not in ex:
                raise ValueError(f"Exercise {i} missing 'question' field")

            # Set defaults
            if "exercise_number" not in ex:
                ex["exercise_number"] = i
            if "type" not in ex:
                ex["type"] = "general"
            if "hint" not in ex:
                ex["hint"] = ""
            if "difficulty" not in ex:
                ex["difficulty"] = "medium"

        return exercises

    def generate_with_answers(
        self, topic: Dict, context: str, num_exercises: int = 5
    ) -> List[Dict]:
        """
        Generate exercises with sample answers/solutions.

        Args:
            topic: Topic dictionary
            context: Relevant content
            num_exercises: Number of exercises

        Returns:
            List of exercises with answer/solution field
        """
        # First generate exercises
        exercises = self.generate_exercises(topic, context, num_exercises)

        # Then generate answers for each
        print("Generating sample answers...")

        for exercise in exercises:
            answer = self._generate_answer(exercise, topic, context)
            exercise["sample_answer"] = answer

        return exercises

    def _generate_answer(self, exercise: Dict, topic: Dict, context: str) -> str:
        """Generate a sample answer for an exercise."""
        answer_prompt = f"""Topic: {topic["title"]}

Context:
{context[:1000]}

Exercise:
{exercise["question"]}

Provide a sample answer or solution to this exercise. Be concise but thorough.

Sample Answer:"""

        response = self.llm_client.simple_prompt(
            answer_prompt, temperature=0.5, max_tokens=500
        )

        return response.strip()

    def validate_answer(self, exercise: Dict, user_answer: str, context: str) -> Dict:
        """
        Validate user's answer to an exercise.

        Args:
            exercise: Exercise dictionary
            user_answer: User's submitted answer
            context: Relevant book content

        Returns:
            Dictionary with:
            - is_correct: Boolean - whether answer is correct
            - feedback: Brief feedback message
            - solution: Full solution with explanation (markdown format)
        """
        validation_prompt = f"""You are evaluating a student's answer and providing the full solution.

Question: {exercise["question"]}

Student's Answer:
{user_answer}

Reference Content:
{context[:1500]}

Evaluate the student's answer and provide a complete response.

Format as JSON:
{{
  "is_correct": true or false,
  "feedback": "Brief encouraging feedback (1-2 sentences) about their answer",
  "solution": "Complete solution with full explanation in markdown format. Include:\n- Whether their answer was correct or not\n- Step-by-step explanation\n- Key concepts involved\n- Additional insights if relevant"
}}

Be encouraging and educational. The solution should teach, not just correct.

Respond ONLY with the JSON object."""

        response = self.llm_client.simple_prompt(
            validation_prompt, temperature=0.5, max_tokens=1500
        )

        # Debug logging
        print(f"\n{'=' * 60}")
        print("LLM Response for validation:")
        print(f"{'=' * 60}")
        print(response[:500] if len(response) > 500 else response)
        if len(response) > 500:
            print(f"... (truncated, total length: {len(response)} chars)")
        print(f"{'=' * 60}\n")

        # Parse response - try multiple strategies
        result = None

        # Strategy 1: Find JSON object
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(0)
                json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
                result = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"Failed to parse validation JSON (strategy 1): {e}")

        # Strategy 2: Try to find JSON in code blocks
        if not result:
            code_block_match = re.search(
                r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL
            )
            if code_block_match:
                try:
                    json_str = code_block_match.group(1)
                    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
                    result = json.loads(json_str)
                    print("Successfully parsed validation JSON from code block")
                except json.JSONDecodeError as e:
                    print(f"Failed to parse validation JSON (strategy 2): {e}")

        # Strategy 3: Try raw response
        if not result:
            try:
                json_str = response.strip()
                json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
                result = json.loads(json_str)
                print("Successfully parsed validation JSON (strategy 3)")
            except json.JSONDecodeError as e:
                print(f"Failed to parse validation JSON (strategy 3): {e}")

        if result:
            # Ensure required fields exist
            if "is_correct" not in result:
                result["is_correct"] = False
            if "feedback" not in result:
                result["feedback"] = "Answer submitted."
            if "solution" not in result:
                result["solution"] = "No solution available."
            return result
        else:
            print(f"Error parsing validation response - all strategies failed")
            print(f"Full response:\n{response}")
            # Fallback to simple response
            return {
                "is_correct": False,
                "feedback": "Unable to validate answer automatically.",
                "solution": response,
            }


if __name__ == "__main__":
    # Simple test
    import sys

    if len(sys.argv) > 1:
        import json

        # Load processed book with contexts
        contexts_file = sys.argv[1]

        with open(contexts_file, "r", encoding="utf-8") as f:
            contexts_data = json.load(f)

        # Load original book data for topics
        book_file = contexts_file.replace("_contexts.json", ".json")
        with open(book_file, "r", encoding="utf-8") as f:
            book_data = json.load(f)

        generator = ExerciseGenerator()

        # Generate exercises for first topic
        topic = book_data["topics"][0]
        context_data = contexts_data["1"]

        print(f"Generating exercises for: {topic['title']}\n")

        exercises = generator.generate_exercises(
            topic, context_data["context"], num_exercises=5
        )

        print("\n" + "=" * 60)
        print("EXERCISES")
        print("=" * 60 + "\n")

        for ex in exercises:
            print(f"{ex['exercise_number']}. [{ex['type'].upper()}] {ex['question']}")
            if ex.get("hint"):
                print(f"   Hint: {ex['hint']}")
            print()
    else:
        print("Usage: python exercise_generator.py <processed_book_contexts.json>")
