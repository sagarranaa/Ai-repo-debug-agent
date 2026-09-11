import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq


PROJECT_ROOT = Path(__file__).resolve().parent

load_dotenv(PROJECT_ROOT / ".env")


def main() -> None:
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to the project's .env file."
        )

    model_name = os.getenv(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile",
    )

    model = ChatGroq(
        model=model_name,
        temperature=0,
        max_tokens=200,
        timeout=30,
        max_retries=2,
    )

    response = model.invoke([
        (
            "system",
            "You are a Python debugging tutor. "
            "Give concise explanations. "
            "Do not claim to have inspected files or executed code.",
        ),
        (
            "human",
            "In two sentences, explain why a failing test "
            "is useful when investigating a bug.",
        ),
    ])

    print(f"Model: {model_name}")
    print("\nResponse:")
    print(response.content)

    print("\nToken usage:")
    print(response.usage_metadata)


if __name__ == "__main__":
    main()