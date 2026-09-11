import argparse
import json
from pathlib import Path
from uuid import uuid4

from langgraph.types import Command

from agent.config import PROJECT_ROOT
from agent.tools.patch_tools import validate_saved_proposal
from agent.workflows.graph import build_repair_graph


def main():
    parser = argparse.ArgumentParser(
        description="Review, apply, and verify a saved patch proposal."
    )
    parser.add_argument(
        "proposal_file",
        help="Path to a proposal JSON file inside the patches folder.",
    )
    args = parser.parse_args()

    proposal_path = Path(args.proposal_file).resolve()
    patches_dir = (PROJECT_ROOT / "patches").resolve()

    if not proposal_path.is_relative_to(patches_dir):
        raise ValueError("Select a proposal inside the patches folder")

    artifact = json.loads(
        proposal_path.read_text(encoding="utf-8")
    )
    proposal = validate_saved_proposal(artifact)

    graph = build_repair_graph()
    run_id = uuid4().hex

    config = {
        "configurable": {
            "thread_id": run_id,
        },
    }

    # Run until LangGraph pauses for your approval.
    paused = graph.invoke(
        {
            "proposal": proposal,
            "status": "awaiting_review",
        },
        config=config,
    )

    interrupts = paused.get("__interrupt__")

    if not interrupts:
        raise RuntimeError(
            "Expected the workflow to pause for review"
        )

    review = interrupts[0].value

    print("\nFILE:", review["relative_path"])
    print("\nEXPLANATION:", review["explanation"])
    print("\nDIFF:\n")
    print(review["diff"])

    print(
        "\nApproval will write this code and execute the demo tests."
    )

    answer = input(
        "Type yes to approve; anything else rejects: "
    )
    approved = answer.strip().lower() == "yes"

    # Resume the same workflow with your decision.
    final = graph.invoke(
        Command(resume=approved),
        config=config,
    )

    print("\nSTATUS:", final["status"])

    if final.get("backup_file"):
        print("BACKUP:", final["backup_file"])

    if final.get("test_result"):
        print("\nTEST OUTPUT:")
        print(final["test_result"]["output"])

    if final["status"] == "verification_failed":
        print(
            "The proposed code remains applied. "
            "The original file is preserved in the backup."
        )

    report_dir = PROJECT_ROOT / "reports"
    report_dir.mkdir(exist_ok=True)

    report_path = report_dir / f"repair_{run_id}.json"
    report_path.write_text(
        json.dumps(final, indent=2),
        encoding="utf-8",
    )

    print("\nREPORT:", report_path)


if __name__ == "__main__":
    main()