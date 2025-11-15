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

    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent
    BACKEND_DIR = Path(__file__).parent
    DATA_DIR = BACKEND_DIR / "data"
    VENUES_FILE = DATA_DIR / "venues.json"

    # Singapore-specific pricing
    GST_RATE: float = 0.09  # 9% GST
    SERVICE_CHARGE_RATE: float = 0.10  # 10% service charge

    # LLM Provider Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")

    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

    # Gemini Configuration
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Agent Configuration
    AGENT_VERBOSE: bool = os.getenv("AGENT_VERBOSE", "true").lower() == "true"

    # Langfuse Configuration
    LANGFUSE_ENABLED: bool = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"
    LANGFUSE_PUBLIC_KEY: Optional[str] = os.getenv("LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY: Optional[str] = os.getenv("LANGFUSE_SECRET_KEY")
    LANGFUSE_BASE_URL: Optional[str] = os.getenv("LANGFUSE_BASE_URL")  # Optional: for self-hosted

    @classmethod
    def get_llm_model(cls) -> str:
        """Get the configured LLM model with provider prefix (for LiteLLM)"""
        if cls.LLM_PROVIDER == "gemini":
            return f"gemini/{cls.GEMINI_MODEL}"
        elif cls.LLM_PROVIDER == "openai":
            return f"openai/{cls.OPENAI_MODEL}"
        else:
            raise ValueError(f"Unsupported LLM provider: {cls.LLM_PROVIDER}")

    @classmethod
    def get_llm_model_id(cls) -> str:
        """Get the LLM model ID for smolagents/LiteLLM"""
        return cls.get_llm_model()

    @classmethod
    def get_llm_api_key(cls) -> Optional[str]:
        """Get the API key for the configured LLM provider"""
        if cls.LLM_PROVIDER == "gemini":
            return cls.GEMINI_API_KEY or cls.GOOGLE_API_KEY
        elif cls.LLM_PROVIDER == "openai":
            return cls.OPENAI_API_KEY
        else:
            raise ValueError(f"Unsupported LLM provider: {cls.LLM_PROVIDER}")


# Convenience instance
config = Config()
