import ast
import hashlib
import json
from difflib import unified_diff
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from agent.config import MAX_FILE_BYTES, PROJECT_ROOT
from agent.model import build_model
from agent.tools.file_tools import _resolve_allowed_file


class PatchProposal(BaseModel):
    """A proposed replacement for the checkout source file."""

    relative_path: Literal["shop/checkout.py"]
    explanation: str = Field(min_length=1, max_length=2000)
    new_content: str = Field(min_length=1, max_length=64_000)


def read_source(relative_path: str) -> bytes:
    """Read an approved file with the existing size limit."""
    path = _resolve_allowed_file(relative_path)

    with path.open("rb") as source:
        raw = source.read(MAX_FILE_BYTES + 1)

    if len(raw) > MAX_FILE_BYTES:
        raise ValueError(f"File too large: {relative_path}")

    return raw


def propose_patch(investigation: str) -> dict:
    """Generate and save a proposal without changing source files."""
    target = "shop/checkout.py"

    context_paths = (
        "README.md",
        target,
        "shop/pricing.py",
        "shop/coupons.py",
        "tests/test_checkout.py",
    )

    snapshots = {
        path: read_source(path)
        for path in context_paths
    }

    context = {
        path: raw.decode("utf-8")
        for path, raw in snapshots.items()
    }

    prompt = (
        PROJECT_ROOT / "prompts" / "patch_proposer.md"
    ).read_text(encoding="utf-8")

    structured_model = build_model().with_structured_output(
        PatchProposal,
        method="function_calling",
    )

    proposal = structured_model.invoke([
        ("system", prompt),
        ("human", json.dumps({
            "investigation": investigation,
            "repository_files": context,
        })),
    ])

    if not isinstance(proposal, PatchProposal):
        raise ValueError("The model did not return a valid proposal")

    new_content = proposal.new_content

    if not new_content.endswith("\n"):
        new_content += "\n"

    if len(new_content.encode("utf-8")) > MAX_FILE_BYTES:
        raise ValueError("Proposed file exceeds the size limit")

    # Parse the code without executing it.
    ast.parse(new_content, filename=target)

    old_content = context[target]

    if new_content == old_content:
        raise ValueError("The proposal contains no change")

    # Reject a proposal if its source context changed during generation.
    for path, original in snapshots.items():
        if read_source(path) != original:
            raise ValueError(
                f"Source changed during generation: {path}. Run again."
            )

    diff = "".join(unified_diff(
        old_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{target}",
        tofile=f"b/{target}",
    ))

    artifact = {
        "status": "proposed",
        "relative_path": target,
        "explanation": proposal.explanation,
        "source_hashes": {
            path: hashlib.sha256(raw).hexdigest()
            for path, raw in snapshots.items()
        },
        "new_content": new_content,
        "diff": diff,
        "verification": "Not applied or tested",
    }

    output_dir = PROJECT_ROOT / "patches"
    output_dir.mkdir(exist_ok=True)

    proposal_id = uuid4().hex[:12]
    proposal_path = output_dir / f"proposal_{proposal_id}.json"

    proposal_path.write_text(
        json.dumps(artifact, indent=2),
        encoding="utf-8",
    )

    return {
        **artifact,
        "proposal_file": str(proposal_path),
    }

EXPECTED_CONTEXT = {
    "README.md",
    "shop/checkout.py",
    "shop/pricing.py",
    "shop/coupons.py",
    "tests/test_checkout.py",
}


def validate_saved_proposal(artifact: dict) -> dict:
    """Validate a proposal against the current repository."""
    proposal = PatchProposal.model_validate(artifact)

    hashes = artifact.get("source_hashes")

    if not isinstance(hashes, dict) or set(hashes) != EXPECTED_CONTEXT:
        raise ValueError("Proposal has missing or unexpected source hashes")

    for relative_path, expected_hash in hashes.items():
        actual_hash = hashlib.sha256(
            read_source(relative_path)
        ).hexdigest()

        if actual_hash != expected_hash:
            raise ValueError(
                f"Source changed: {relative_path}. "
                "Generate and review a fresh proposal."
            )

    new_content = proposal.new_content

    if len(new_content.encode("utf-8")) > MAX_FILE_BYTES:
        raise ValueError("Proposed file exceeds the size limit")

    ast.parse(new_content, filename=proposal.relative_path)

    old_content = read_source(
        proposal.relative_path
    ).decode("utf-8")

    if old_content == new_content:
        raise ValueError("Proposal contains no change")
    def display_lines(text):
        return [line + "\n" for line in text.splitlines()]

    diff = "".join(unified_diff(
        display_lines(old_content),
        display_lines(new_content),
        fromfile=f"a/{proposal.relative_path}",
        tofile=f"b/{proposal.relative_path}",
    ))

    if old_content.endswith("\n") != new_content.endswith("\n"):
        diff += (
            "\nFinal newline: "
            f"{old_content.endswith(chr(10))} -> "
            f"{new_content.endswith(chr(10))}\n"
        )

    return {
        **artifact,
        **proposal.model_dump(),
        "diff": diff,
    }


def apply_saved_proposal(artifact: dict) -> dict:
    """Recheck the source, back it up, then write the proposal."""
    artifact = validate_saved_proposal(artifact)

    target = _resolve_allowed_file(artifact["relative_path"])
    original = read_source(artifact["relative_path"])

    backup_dir = PROJECT_ROOT / "patches" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_path = backup_dir / f"checkout_{uuid4().hex}.py.bak"

    with backup_path.open("xb") as backup:
        backup.write(original)

    target.write_bytes(artifact["new_content"].encode("utf-8"))

    return {
        "status": "applied",
        "backup_file": str(backup_path),
    }