import os
import subprocess
import sys

from agent.config import REPO_ROOT
from agent.tools.file_tools import _resolve_allowed_file


ALLOWED_TEST_FILES = {"tests/test_checkout.py"}
TEST_TIMEOUT_SECONDS = 20
MAX_OUTPUT_CHARS = 12_000


def run_tests(
    test_path: str = "tests/test_checkout.py",
) -> dict:
    """Run an approved test file inside the demo repository."""
    if test_path not in ALLOWED_TEST_FILES:
        raise ValueError("This test file is not allowed")

    _resolve_allowed_file(test_path)

    command = [
        sys.executable,
        "-m",
        "pytest",
        test_path,
        "-q",
        "--tb=short",
        "-p",
        "no:cacheprovider",
    ]

    # Pass only selected environment variables to the child process.
    environment = {
        name: os.environ[name]
        for name in (
            "PATH", "SystemRoot", "WINDIR",
            "TEMP", "TMP", "LANG",
        )
        if name in os.environ
    }

    environment.update({
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
    })

    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
            timeout=TEST_TIMEOUT_SECONDS,
            shell=False,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "test_path": test_path,
            "status": "timeout",
            "exit_code": None,
            "output": (
                f"Test execution exceeded "
                f"{TEST_TIMEOUT_SECONDS} seconds."
            ),
            "output_truncated": False,
        }

    status = {
        0: "passed",
        1: "failed",
    }.get(completed.returncode, "error")

    return {
        "test_path": test_path,
        "status": status,
        "exit_code": completed.returncode,
        "output": completed.stdout[:MAX_OUTPUT_CHARS],
        "output_truncated": (
            len(completed.stdout) > MAX_OUTPUT_CHARS
        ),
    }