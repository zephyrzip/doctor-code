import os
from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# ==========================================
# 1. The Pydantic Blueprint
# ==========================================
class CodeFinding(BaseModel):
    """Strict schema for a single code review finding."""
    filename: str = Field(description="The exact name of the file where the issue was found.")
    line_number: int = Field(description="The specific line number where the issue occurs.")
    category: str = Field(description="Categorize as: Security Vulnerability, Critical Logic Bug, or Performance/Resource Flaw.")
    bug_description: str = Field(description="A clear, concise explanation of the issue and why it is problematic.")
    suggested_fix: str = Field(description="An actionable suggestion or exact code snippet to resolve the issue.")

class ReviewResult(BaseModel):
    """The root schema that forces the AI to return an array of findings."""
    findings: List[CodeFinding] = Field(description="A list of critical issues found in the provided git diff.")


# ==========================================
# 2. The Abstract Base Class (Provider Pattern)
# ==========================================
class BaseReviewer(ABC):
    """
    The template interface. Any AI model we plug in later (Claude, GPT-4) 
    must inherit from this and implement the review_code method.
    """
    @abstractmethod
    def review_code(self, diff_text: str) -> ReviewResult:
        """Analyzes a git diff and returns structured review findings."""
        pass


# ==========================================
# 3. The Gemini Adapter
# ==========================================
class GeminiReviewer(BaseReviewer):
    """
    Concrete implementation utilizing the modern google-genai client.
    """
    def __init__(self):
        # Securely loads your API key from the environment/dotenv
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("CRITICAL: GEMINI_API_KEY environment variable is not set. Check your .env file.")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-3.5-flash" # Swap to gemini-2.5-flash for speed/cost if desired

    def review_code(self, diff_text: str) -> ReviewResult:
        # The prompt strategy to keep the AI focused
        system_instruction = (
            "You are an elite senior software engineer reviewing a pull request diff. "
            "Scan exclusively for: Security Vulnerabilities, Critical Logic Bugs, and Performance/Resource Flaws. "
            "Completely ignore minor stylistic formatting or preference-based changes. "
            "If no critical issues are found, return an empty list."
        )

        prompt = f"Please analyze the following git diff:\n\n{diff_text}"

        # Streaming the diff to the Gemini Pro API and enforcing our Pydantic schema
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=ReviewResult,
                temperature=0.1, # Low temperature for highly analytical, deterministic output
            ),
        )

        # Parse the rigid JSON text directly into our Pydantic object
        return ReviewResult.model_validate_json(response.text)