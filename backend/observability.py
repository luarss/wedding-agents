"""
Observability integration for tracking token usage and costs
"""

from typing import Optional
from langfuse import Langfuse
from backend.config import config


class ObservabilityManager:
    """Manages observability integrations like Langfuse"""

    _instance: Optional['ObservabilityManager'] = None
    _langfuse: Optional[Langfuse] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._setup_langfuse()
            self._setup_agent_instrumentation()

    def _setup_langfuse(self):
        """Initialize Langfuse if enabled"""
        if config.LANGFUSE_ENABLED:
            try:
                langfuse_kwargs = {}

                # Add base URL if provided (for self-hosted)
                if config.LANGFUSE_BASE_URL:
                    langfuse_kwargs["host"] = config.LANGFUSE_BASE_URL

                # Add keys if provided
                if config.LANGFUSE_PUBLIC_KEY and config.LANGFUSE_SECRET_KEY:
                    langfuse_kwargs["public_key"] = config.LANGFUSE_PUBLIC_KEY
                    langfuse_kwargs["secret_key"] = config.LANGFUSE_SECRET_KEY

                self._langfuse = Langfuse(**langfuse_kwargs)
                print(f"✅ Langfuse initialized")
            except Exception as e:
                print(f"⚠️  Failed to initialize Langfuse: {e}")

    def _setup_agent_instrumentation(self):
        """Initialize instrumentation for agent frameworks to capture token usage"""
        if config.LANGFUSE_ENABLED:
            try:
                from openinference.instrumentation.smolagents import SmolagentsInstrumentor

                # Instrument smolagents to capture detailed telemetry
                SmolagentsInstrumentor().instrument()
                print(f"✅ smolagents instrumentation initialized for token tracking")
            except ImportError:
                print("⚠️  openinference-instrumentation-smolagents not installed. Token tracking unavailable.")
            except Exception as e:
                print(f"⚠️  Failed to initialize smolagents instrumentation: {e}")

    @property
    def langfuse(self) -> Optional[Langfuse]:
        """Get Langfuse client if enabled"""
        return self._langfuse

    def is_enabled(self) -> bool:
        """Check if observability is enabled"""
        return self._langfuse is not None


# Singleton instance
observability = ObservabilityManager()
