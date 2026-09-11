from langgraph.types import interrupt

from agent.tools.patch_tools import apply_saved_proposal
from agent.tools.test_runner import run_tests
from agent.workflows.state import RepairState


def review_patch(state: RepairState) -> dict:
    proposal = state["proposal"]

    decision = interrupt({
        "question": "Apply this change and run the checkout tests?",
        "relative_path": proposal["relative_path"],
        "explanation": proposal["explanation"],
        "diff": proposal["diff"],
    })

    approved = decision is True

    return {
        "approved": approved,
        "status": "approved" if approved else "rejected",
    }


def apply_patch(state: RepairState) -> dict:
    if state.get("approved") is not True:
        raise ValueError("Patch application requires approval")

    return apply_saved_proposal(state["proposal"])


def verify_patch(state: RepairState) -> dict:
    result = run_tests("tests/test_checkout.py")

    return {
        "test_result": result,
        "status": (
            "verified"
            if result["status"] == "passed"
            else "verification_failed"
        ),
    }