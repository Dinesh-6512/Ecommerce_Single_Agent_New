import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Ensure environment variables are loaded from backend/.env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"


def get_groq_model(
    model_name: Optional[str] = None,
    temperature: float = 0.0,
    **kwargs
) -> ChatGroq:
    """
    Instantiate and return a ChatGroq LLM using GROQ_API_KEY and GROQ_MODEL from environment.
    Strictly avoids hard-coding or printing the API key.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY environment variable is missing. "
            "Please configure GROQ_API_KEY in backend/.env"
        )

    selected_model = model_name or os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)

    return ChatGroq(
        groq_api_key=api_key,
        model_name=selected_model,
        temperature=temperature,
        **kwargs
    )
