import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from agent.config import PROJECT_ROOT


def build_model():
    """Create the Groq chat model used by the investigator."""
    load_dotenv(PROJECT_ROOT / ".env")

    if not os.getenv("GROQ_API_KEY"):
        raise ValueError("GROQ_API_KEY is missing from .env")

    return ChatGroq(
        model=os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b",
        ),
        temperature=0,
        max_tokens=2048,
        timeout=60,
        max_retries=2,
    )