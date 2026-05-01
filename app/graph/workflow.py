from __future__ import annotations

from langgraph.graph import StateGraph, END

from app.graph.state import MerlinState
from app.graph.nodes import (
    research_node,
    evidence_node,
    planner_node,
    debate_node,
    judge_node,
    builder_node,
    debugger_node,
    debug_research_node,
    finalize_node,
)
from app.graph.router import route_after_judge, route_after_debug


def build_graph():
    """Compile the Merlin LangGraph workflow."""
    graph = StateGraph(MerlinState)

    # Register nodes
    graph.add_node("research_node", research_node)
    graph.add_node("evidence_node", evidence_node)
    graph.add_node("planner_node", planner_node)
    graph.add_node("debate_node", debate_node)
    graph.add_node("judge_node", judge_node)
    graph.add_node("builder_node", builder_node)
    graph.add_node("debugger_node", debugger_node)
    graph.add_node("debug_research_node", debug_research_node)
    graph.add_node("finalize_node", finalize_node)

    # Entry point
    graph.set_entry_point("research_node")

    # Fixed edges
    graph.add_edge("research_node", "evidence_node")
    graph.add_edge("evidence_node", "planner_node")
    graph.add_edge("planner_node", "debate_node")
    graph.add_edge("debate_node", "judge_node")

    # Conditional: judge routes to builder or back to planner/research/finalize
    graph.add_conditional_edges(
        "judge_node",
        route_after_judge,
        {
            "builder_node": "builder_node",
            "planner_node": "planner_node",
            "research_node": "research_node",
            "finalize_node": "finalize_node",
        },
    )

    # Builder always goes to debugger
    graph.add_edge("builder_node", "debugger_node")

    # Conditional: debug routes to finalize, retry, or research
    graph.add_conditional_edges(
        "debugger_node",
        route_after_debug,
        {
            "finalize_node": "finalize_node",
            "debugger_node": "debugger_node",
            "debug_research_node": "debug_research_node",
        },
    )

    graph.add_edge("debug_research_node", "debugger_node")
    graph.add_edge("finalize_node", END)

    return graph.compile()


# Compile once at import time — build_graph() is pure graph construction
# (no I/O, no network), so this is safe and avoids a race condition when
# multiple async workers call get_graph() concurrently before init completes.
_graph = build_graph()


def get_graph():
    return _graph
