from pathlib import Path

from agent.config import (
    ALLOWED_FILES,
    MAX_FILE_BYTES,
    REPO_ROOT,
)


def _resolve_allowed_file(relative_path: str) -> Path:
    """Validate a requested demo file before accessing it."""

    if relative_path not in ALLOWED_FILES:
        raise ValueError("This file is not allowed")

    root = REPO_ROOT.resolve()
    path = (root / relative_path).resolve()

    if not path.is_relative_to(root):
        raise ValueError("File resolves outside the demo repository")

    if not path.is_file():
        raise FileNotFoundError(
            f"Demo file does not exist: {relative_path}"
        )

    return path


def list_files() -> list[str]:
    """List the approved files available for investigation."""

    available_files = []

    for relative_path in ALLOWED_FILES:
        _resolve_allowed_file(relative_path)
        available_files.append(relative_path)

    return sorted(available_files)


def read_file(
    relative_path: str,
    start_line: int = 1,
    end_line: int = 120,
) -> dict:
    """Read up to 120 lines from an approved demo file."""

    if start_line < 1 or end_line < start_line:
        raise ValueError("Invalid line range")

    if end_line - start_line + 1 > 120:
        raise ValueError("Read at most 120 lines per call")

    path = _resolve_allowed_file(relative_path)

    with path.open("rb") as file:
        raw = file.read(MAX_FILE_BYTES + 1)

    if len(raw) > MAX_FILE_BYTES:
        raise ValueError("File exceeds the reading size limit")

    lines = raw.decode("utf-8").splitlines()

    selected_lines = [
        f"{number}: {line}"
        for number, line in enumerate(lines, start=1)
        if start_line <= number <= end_line
    ]

    return {
        "path": relative_path,
        "total_lines": len(lines),
        "content": "\n".join(selected_lines),
        "has_more": len(lines) > end_line,
    }

def search_code(query: str) -> dict:
    """Search approved files for literal text, ignoring case."""
    if not query.strip():
        raise ValueError("Search query cannot be empty")

    matches = []
    limit = 50

    for relative_path in list_files():
        start_line = 1

        while True:
            page = read_file(
                relative_path,
                start_line=start_line,
                end_line=start_line + 119,
            )

            for numbered_line in page["content"].splitlines():
                number, _, text = numbered_line.partition(": ")

                if query.casefold() in text.casefold():
                    matches.append({
                        "path": relative_path,
                        "line": int(number),
                        "text": text,
                    })

                    if len(matches) > limit:
                        return {
                            "query": query,
                            "matches": matches[:limit],
                            "truncated": True,
                        }

            if not page["has_more"]:
                break

            start_line += 120

    return {
        "query": query,
        "matches": matches,
        "truncated": False,
    }