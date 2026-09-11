from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from agent.workflows.nodes import (
    apply_patch,
    review_patch,
    verify_patch,
)
from agent.workflows.state import RepairState


def route_after_review(state: RepairState) -> str:
    return "apply" if state["approved"] else "reject"


def build_repair_graph():
    graph = StateGraph(RepairState)

    graph.add_node("review", review_patch)
    graph.add_node("apply", apply_patch)
    graph.add_node("verify", verify_patch)

    graph.add_edge(START, "review")

    graph.add_conditional_edges(
        "review",
        route_after_review,
        {
            "apply": "apply",
            "reject": END,
        },
    )

    graph.add_edge("apply", "verify")
    graph.add_edge("verify", END)

    return graph.compile(checkpointer=InMemorySaver())