"""
Centralized configuration for the wedding agent
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""

    # LLM Provider Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")

    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

    # Gemini Configuration
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # CrewAI Configuration
    CREW_VERBOSE: bool = os.getenv("CREW_VERBOSE", "true").lower() == "true"

    @classmethod
    def get_llm_model(cls) -> str:
        """Get the configured LLM model with provider prefix"""
        if cls.LLM_PROVIDER == "gemini":
            return f"gemini/{cls.GEMINI_MODEL}"
        elif cls.LLM_PROVIDER == "openai":
            return f"openai/{cls.OPENAI_MODEL}"
        else:
            raise ValueError(f"Unsupported LLM provider: {cls.LLM_PROVIDER}")


# Convenience instance
config = Config()
