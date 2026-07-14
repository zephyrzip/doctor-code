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
    file: str = Field(..., description="The name of the file where the issue was found.")
    line: int = Field(..., description="The exact line number of the issue.")
    category: str = Field(..., description="The severity/type (e.g., Security, Critical Logic Bug).")
    description: str = Field(..., description="Clear explanation of what the bug is and why it fails.")
    suggestion: str = Field(..., description="Actionable code fix for the developer.")

class ReviewResult(BaseModel):
    """The root schema that forces the AI to return an array of findings."""
    summary: str = Field(..., description="A concise, high-level summary of the architectural changes, intent, and overall scope of this Pull Request.")
    findings: List[CodeFinding] = Field(default_factory=list, description="A list of specific code bugs or vulnerabilities found in the diff.")

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
            "You are an elite senior software engineer performing a code review. "
            "Your task has two strict requirements:\n"
            "1. SUMMARY: First, analyze the provided git diff and write a concise, high-level summary of the architectural changes, intent, and overall scope of this Pull Request.\n"
            "2. FINDINGS: Next, scan the code exclusively for Security Vulnerabilities, Critical Logic Bugs, and Resource/Performance Flaws.\n"
            "If the code is perfectly clean and has no critical issues, return your brilliant summary and an empty list for the findings."
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
            "You are an elite senior software engineer performing a code review. "
            "Your task has two strict requirements:\n"
            "1. SUMMARY: First, analyze the provided git diff and write a concise, high-level summary of the architectural changes, intent, and overall scope of this Pull Request.\n"
            "2. FINDINGS: Next, scan the code exclusively for Security Vulnerabilities, Critical Logic Bugs, and Resource/Performance Flaws.\n"
            "If the code is perfectly clean and has no critical issues, return your brilliant summary and an empty list for the findings."
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
# 5. The Anthropic Adapter (Claude Sonnet 5)
# ==========================================
class AnthropicReviewer(BaseReviewer):
    """Concrete implementation utilizing the Anthropic SDK."""
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("CRITICAL: ANTHROPIC_API_KEY environment variable is not set.")
            
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model_name = "claude-sonnet-5"

    def review_code(self, diff_text: str) -> ReviewResult:
        # Anthropic doesn't have a direct `.parse()` method yet, so we inject the 
        # schema directly into the system prompt to force compliance.
        system_instruction = (
            "You are an elite senior software engineer performing a code review. "
            "Your task has two strict requirements:\n"
            "1. SUMMARY: First, analyze the provided git diff and write a concise, high-level summary of the architectural changes, intent, and overall scope of this Pull Request.\n"
            "2. FINDINGS: Next, scan the code exclusively for Security Vulnerabilities, Critical Logic Bugs, and Resource/Performance Flaws.\n"
            "If the code is perfectly clean and has no critical issues, return your brilliant summary and an empty list for the findings.\n"
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

        # Parse the raw JSON string back into our Pydantic object.
        # raw_decode only requires a valid JSON value to START at index i - it
        # doesn't care what comes after (trailing markdown fences, commentary,
        # etc.), unlike json.loads() which needs the whole remaining string to be valid JSON.
        raw_text = response.content[0].text
        decoder = json.JSONDecoder()
        for i, char in enumerate(raw_text):
            if char != '{':
                continue
            try:
                parsed_data, _ = decoder.raw_decode(raw_text, i)
                return ReviewResult(**parsed_data)
            except json.JSONDecodeError:
                # Not a valid JSON object starting at this index, keep looking
                continue

        raise ValueError("Could not find a valid JSON object in the response.")