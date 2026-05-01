from __future__ import annotations

from app.graph.state import MerlinState


def route_after_judge(state: MerlinState) -> str:
    """Route after The Crown's decision."""
    decision = state.judge_decision

    if decision is None:
        return "finalize_node"

    if decision == "APPROVED":
        # Research mode doesn't need build/debug — skip straight to finalize
        if state.mode == "research":
            return "finalize_node"
        return "builder_node"

    if decision == "EVIDENCE_INSUFFICIENT":
        # Only loop back to research if we haven't exceeded debate rounds
        if state.debate_round < state.max_debate_rounds:
            return "research_node"
        return "finalize_node"

    # REVISION_REQUIRED or CONTRADICTION_FOUND
    if state.debate_round >= state.max_debate_rounds:
        # Force finalize to prevent infinite loop
        return "finalize_node"

    return "planner_node"


def route_after_debug(state: MerlinState) -> str:
    """Route after Sir Bors' debug decision."""
    decision = state.debug_decision

    if decision is None:
        return "finalize_node"

    if decision == "SUCCESS":
        return "finalize_node"

    if decision == "DOC_RESEARCH_REQUIRED" and state.debug_round < state.max_debug_rounds:
        return "debug_research_node"

    if decision == "PATCH_REQUIRED" and state.debug_round < state.max_debug_rounds:
        return "debugger_node"

    # BLOCKED or rounds exhausted
    return "finalize_node"
