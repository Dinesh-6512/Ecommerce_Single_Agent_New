"""
Langfuse Tracing integration for the 'Ask the Store' agent.

Supports Langfuse v5 (OpenTelemetry-based) and earlier versions seamlessly.
Reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, and LANGFUSE_HOST / LANGFUSE_BASE_URL.
Never logs passwords, secret keys, auth tokens, or personal user data.
Provides graceful no-op fallbacks if Langfuse keys are not configured.
"""
import os
from pathlib import Path
from typing import Optional, Tuple, Any, Dict, List
from dotenv import load_dotenv

# Ensure environment variables are loaded from backend/.env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class NoOpSpan:
    """Safe no-op object used when Langfuse is not configured or fails to initialize."""
    def end(self, *args, **kwargs):
        pass

    def update(self, *args, **kwargs):
        pass


class NoOpTrace:
    """Safe no-op trace object used when Langfuse is not configured."""
    def span(self, *args, **kwargs):
        return NoOpSpan()

    def generation(self, *args, **kwargs):
        return NoOpSpan()

    def update(self, *args, **kwargs):
        pass

    def end(self, *args, **kwargs):
        pass


class LangfuseObservationSpan:
    """Wrapper around Langfuse observation to maintain clean span API across versions."""
    def __init__(self, observation: Any):
        self._obs = observation

    def end(self, output: Any = None, level: Optional[str] = None, status_message: Optional[str] = None, **kwargs):
        if not self._obs:
            return
        try:
            update_kwargs: Dict[str, Any] = {}
            if output is not None:
                update_kwargs["output"] = output
            if level is not None:
                update_kwargs["level"] = level
            if status_message is not None:
                update_kwargs["status_message"] = status_message
            if update_kwargs and hasattr(self._obs, "update"):
                self._obs.update(**update_kwargs)
            if hasattr(self._obs, "end"):
                self._obs.end()
        except Exception as e:
            print(f"[Langfuse Span Warning] {e}")

    def update(self, **kwargs):
        if not self._obs:
            return
        try:
            if hasattr(self._obs, "update"):
                self._obs.update(**kwargs)
        except Exception as e:
            print(f"[Langfuse Update Warning] {e}")


class LangfuseTraceWrapper:
    """Wrapper around Langfuse root trace / agent observation."""
    def __init__(self, root_obs: Any, client: Any):
        self._obs = root_obs
        self._client = client

    def span(self, name: str, input: Any = None, **kwargs) -> Any:
        if not self._obs:
            return NoOpSpan()
        try:
            if hasattr(self._obs, "start_observation"):
                child = self._obs.start_observation(name=name, as_type="span", input=input)
                return LangfuseObservationSpan(child)
            elif hasattr(self._obs, "span"):
                return self._obs.span(name=name, input=input, **kwargs)
        except Exception as e:
            print(f"[Langfuse Span Creation Warning] {e}")
        return NoOpSpan()

    def generation(self, name: str, model: Optional[str] = None, input: Any = None, model_parameters: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        if not self._obs:
            return NoOpSpan()
        try:
            if hasattr(self._obs, "start_observation"):
                gen = self._obs.start_observation(
                    name=name,
                    as_type="generation",
                    model=model,
                    input=input,
                    model_parameters=model_parameters or {}
                )
                return LangfuseObservationSpan(gen)
            elif hasattr(self._obs, "generation"):
                return self._obs.generation(name=name, model=model, input=input, model_parameters=model_parameters, **kwargs)
        except Exception as e:
            print(f"[Langfuse Generation Creation Warning] {e}")
        return NoOpSpan()

    def update(self, **kwargs):
        if not self._obs:
            return
        try:
            update_kwargs: Dict[str, Any] = {}
            if "output" in kwargs:
                update_kwargs["output"] = kwargs["output"]
            if "level" in kwargs:
                update_kwargs["level"] = kwargs["level"]
            if "status_message" in kwargs:
                update_kwargs["status_message"] = kwargs["status_message"]
            if "metadata" in kwargs:
                update_kwargs["metadata"] = kwargs["metadata"]

            if hasattr(self._obs, "update"):
                self._obs.update(**update_kwargs)
        except Exception as e:
            print(f"[Langfuse Trace Update Warning] {e}")

    def end(self, **kwargs):
        if self._obs and hasattr(self._obs, "end"):
            try:
                self._obs.end()
            except Exception:
                pass


def get_langfuse_client() -> Optional[Any]:
    """
    Returns an initialized Langfuse client if environment credentials exist.
    """
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        return None

    try:
        from langfuse import Langfuse
        client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )
        return client
    except Exception as e:
        print(f"[Langfuse Tracing Warning] Failed to initialize client: {e}")
        return None


def create_agent_trace(user_id: int, question: str) -> Tuple[Any, Optional[Any]]:
    """
    Creates and returns a Langfuse trace for an agent request.
    Compatible with both Langfuse v5 and legacy v2/v3 SDK.
    Returns (trace, client). If unconfigured, returns (NoOpTrace(), None).
    """
    client = get_langfuse_client()
    if not client:
        return NoOpTrace(), None

    metadata = {
        "user_id": str(user_id),
        "environment": os.getenv("ENV", "production"),
        "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    }

    try:
        # Langfuse v5 (start_observation)
        if hasattr(client, "start_observation"):
            root_obs = client.start_observation(
                name="ask-the-store-flow",
                as_type="agent",
                input={"question": question},
                metadata=metadata
            )
            return LangfuseTraceWrapper(root_obs, client), client

        # Langfuse v2/v3 legacy (client.trace)
        if hasattr(client, "trace"):
            trace = client.trace(
                name="ask-the-store-flow",
                user_id=str(user_id),
                input={"question": question},
                tags=["store-agent"],
                metadata=metadata
            )
            return trace, client

        return NoOpTrace(), client
    except Exception as e:
        print(f"[Langfuse Trace Creation Error] {e}")
        return NoOpTrace(), None
