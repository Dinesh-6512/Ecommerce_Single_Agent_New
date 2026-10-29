"""
Temporary test script to verify Groq model integration.
Sends 'Say hello in one line' and prints the response.
Run with: python test_groq.py
Delete after testing.
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend folder is in Python module search path
backend_path = Path(__file__).resolve().parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Load environment configuration from backend/.env
env_path = backend_path / ".env"
load_dotenv(dotenv_path=env_path)

try:
    from agent.llm import get_groq_model
except ImportError:
    from backend.agent.llm import get_groq_model


def main():
    llm = get_groq_model()
    response = llm.invoke("Say hello in one line")
    print(response.content)


if __name__ == "__main__":
    main()
