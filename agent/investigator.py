from langchain.agents import create_agent
from langchain.tools import tool

from agent.config import PROJECT_ROOT
from agent.model import build_model
from agent.tools.file_tools import (
    list_files,
    read_file,
    search_code,
)
from agent.tools.test_runner import run_tests


def tool_result(function, **kwargs) -> dict:
    """Return expected tool errors as feedback to the model."""
    try:
        return {
            "ok": True,
            "result": function(**kwargs),
        }
    except (ValueError, OSError, UnicodeError) as exc:
        return {
            "ok": False,
            "error": str(exc),
        }


@tool
def list_repository_files() -> dict:
    """List approved repository files available for investigation."""
    return tool_result(list_files)


@tool
def read_repository_file(
    relative_path: str,
    start_line: int = 1,
    end_line: int = 120,
) -> dict:
    """Read an approved file with line numbers, at most 120 lines."""
    return tool_result(
        read_file,
        relative_path=relative_path,
        start_line=start_line,
        end_line=end_line,
    )


@tool
def search_repository_code(query: str) -> dict:
    """Find literal text in approved files, ignoring case."""
    return tool_result(search_code, query=query)


@tool
def run_repository_tests(
    test_path: str = "tests/test_checkout.py",
) -> dict:
    """Run approved demo tests and return their status and output."""
    return tool_result(run_tests, test_path=test_path)


def build_investigator():
    """Build an agent that investigates using repository tools."""
    prompt_path = PROJECT_ROOT / "prompts" / "investigator.md"

    return create_agent(
        model=build_model(),
        tools=[
            list_repository_files,
            read_repository_file,
            search_repository_code,
            run_repository_tests,
        ],
        system_prompt=prompt_path.read_text(encoding="utf-8"),
    )


@tool
def read_repository_file(
    relative_path: str,
    start_line: int = 1,
) -> dict:
    """Read up to 120 lines of an approved repository file.

    Start at line 1 unless continuing a previous read.
    If has_more is true, increase start_line by 120.
    """
    return tool_result(
        read_file,
        relative_path=relative_path,
        start_line=start_line,
        end_line=start_line + 119,
    )