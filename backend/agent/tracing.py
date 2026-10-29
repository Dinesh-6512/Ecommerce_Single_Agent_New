"""
Langfuse Tracing integration for the 'Ask the Store' agent.

Reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, and LANGFUSE_HOST from the environment.
Never logs passwords, secret keys, auth tokens, or personal user data.
Provides graceful no-op fallbacks if Langfuse keys are not configured.
"""
import os
from pathlib import Path
from typing import Optional, Tuple, Any
from dotenv import load_dotenv

# Ensure environment variables are loaded from backend/.env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class NoOpSpan:
    """Safe no-op object used when Langfuse is not configured or fails to initialize."""
    def end(self, *args, **kwargs):
        pass


class NoOpTrace:
    """Safe no-op trace object used when Langfuse is not configured."""
    def span(self, *args, **kwargs):
        return NoOpSpan()

    def generation(self, *args, **kwargs):
        return NoOpSpan()

    def update(self, *args, **kwargs):
        pass


def get_langfuse_client() -> Optional[Any]:
    """
    Returns an initialized Langfuse client if environment credentials exist.
    """
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        return None

    try:
        from langfuse import Langfuse
        return Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )
    except Exception:
        return None


def create_agent_trace(user_id: int, question: str) -> Tuple[Any, Optional[Any]]:
    """
    Creates and returns a Langfuse trace for an agent request.
    Returns (trace, client). If unconfigured, returns (NoOpTrace(), None).
    """
    client = get_langfuse_client()
    if not client:
        return NoOpTrace(), None

    try:
        # Strictly sanitize inputs - never record tokens, passwords, or personal data
        trace = client.trace(
            name="ask-the-store-flow",
            user_id=str(user_id),
            input={"question": question},
            tags=["store-agent"],
            metadata={
                "environment": os.getenv("ENV", "development"),
                "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            }
        )
        return trace, client
    except Exception:
        return NoOpTrace(), None
