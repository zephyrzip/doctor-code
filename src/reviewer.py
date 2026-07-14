import os
from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel, Field

from google import genai
from google.genai import types

import openai
import anthropic
import re
import json

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
        self.model_name = "gemini-flash-latest" 

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

# ==========================================
# 4. The OpenAI Adapter (GPT-4o)
# ==========================================
class OpenAIReviewer(BaseReviewer):
    """Concrete implementation utilizing the OpenAI SDK and Structured Outputs."""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("CRITICAL: OPENAI_API_KEY environment variable is not set.")
            
        self.client = openai.OpenAI(api_key=api_key)
        self.model_name = "gpt-4o" 

    def review_code(self, diff_text: str) -> ReviewResult:
        system_instruction = (
            "You are an elite senior software engineer reviewing a pull request diff. "
            "Scan exclusively for: Security Vulnerabilities, Critical Logic Bugs, and Performance/Resource Flaws. "
            "Completely ignore minor stylistic formatting or preference-based changes. "
            "If no critical issues are found, return an empty list."
        )

        prompt = f"Please analyze the following git diff:\n\n{diff_text}"

        # OpenAI's `.parse()` method automatically enforces our Pydantic schema!
        response = self.client.beta.chat.completions.parse(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            response_format=ReviewResult,
            temperature=0.1,
        )

        # Returns the perfectly parsed Pydantic object
        return response.choices[0].message.parsed


# ==========================================
# 5. The Anthropic Adapter (Claude 3.5 Sonnet)
# ==========================================
class AnthropicReviewer(BaseReviewer):
    """Concrete implementation utilizing the Anthropic SDK."""
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("CRITICAL: ANTHROPIC_API_KEY environment variable is not set.")
            
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model_name = "claude-3-5-sonnet-20241022"

    def review_code(self, diff_text: str) -> ReviewResult:
        # Anthropic doesn't have a direct `.parse()` method yet, so we inject the 
        # schema directly into the system prompt to force compliance.
        system_instruction = (
            "You are an elite senior software engineer reviewing a pull request diff. "
            "Scan exclusively for: Security Vulnerabilities, Critical Logic Bugs, and Performance/Resource Flaws. "
            "If no critical issues are found, return an empty list. "
            "You MUST return ONLY valid JSON matching this exact schema. No markdown, no conversational text:\n"
            f"{ReviewResult.model_json_schema()}"
        )

        prompt = f"Please analyze the following git diff:\n\n{diff_text}"

        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=2000,
            temperature=0.1,
            system=system_instruction,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Parse the raw JSON string back into our Pydantic object
        raw_text = response.content[0].text
        # 1. Find the first occurrence of '{'
        start_index = raw_text.find('{')
        # 2. Find the last occurrence of '}'
        end_index = raw_text.rfind('}')
        
        if start_index == -1 or end_index == -1:
            raise ValueError("No JSON object found in response.")
            
        json_str = raw_text[start_index : end_index + 1]
        
        # 3. Use the built-in json library to validate the full structure 
        # before passing to Pydantic
        try:
            parsed_data = json.loads(json_str)
            return ReviewResult(**parsed_data)
        except json.JSONDecodeError as e:
            # If standard JSON fails, your Pydantic model will also fail, 
            # so we catch it here to give a clear error.
            raise ValueError(f"Failed to parse nested JSON: {e}")