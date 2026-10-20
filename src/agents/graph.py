from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from src.agents.nodes import critique_node, draft_node, research_node
from src.agents.state import AgentState


def build_research_graph() -> Any:
    workflow = StateGraph(AgentState)

    workflow.add_node("research", research_node)
    workflow.add_node("draft", draft_node)
    workflow.add_node("critique", critique_node)

    workflow.add_edge(START, "research")
    workflow.add_edge("research", "draft")
    workflow.add_edge("draft", "critique")

    workflow.add_conditional_edges(
        "critique",
        _critique_router,
        {
            "draft": "draft",
            "end": END,
        },
    )

    return workflow.compile()


def _critique_router(state: AgentState) -> str:
    critique = state.get("critique") or {}
    revisions = state.get("revision_count", 0)
    needs_revision = critique.get("needs_revision", False)
    if needs_revision and revisions < 3:
        return "draft"
    return "end"
