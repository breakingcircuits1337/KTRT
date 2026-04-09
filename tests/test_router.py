from __future__ import annotations

from app.graph.router import route_after_judge, route_after_debug
from app.graph.state import MerlinState


def _state(**kwargs) -> MerlinState:
    defaults = dict(query="test", run_id="quest_test", max_debate_rounds=3, max_debug_rounds=3)
    defaults.update(kwargs)
    return MerlinState(**defaults)


class TestJudgeRouter:
    def test_approved_build_mode_goes_to_builder(self):
        state = _state(judge_decision="APPROVED", mode="build")
        assert route_after_judge(state) == "builder_node"

    def test_approved_research_mode_goes_to_finalize(self):
        state = _state(judge_decision="APPROVED", mode="research")
        assert route_after_judge(state) == "finalize_node"

    def test_approved_default_mode_goes_to_builder(self):
        # default mode is "research" per MerlinState — verify it finalizes
        state = _state(judge_decision="APPROVED")
        assert route_after_judge(state) == "finalize_node"

    def test_revision_within_rounds_goes_to_planner(self):
        state = _state(judge_decision="REVISION_REQUIRED", debate_round=1)
        assert route_after_judge(state) == "planner_node"

    def test_revision_at_max_rounds_goes_to_finalize(self):
        state = _state(judge_decision="REVISION_REQUIRED", debate_round=3)
        assert route_after_judge(state) == "finalize_node"

    def test_evidence_insufficient_within_rounds_goes_to_research(self):
        state = _state(judge_decision="EVIDENCE_INSUFFICIENT", debate_round=1)
        assert route_after_judge(state) == "research_node"

    def test_evidence_insufficient_at_max_rounds_goes_to_finalize(self):
        state = _state(judge_decision="EVIDENCE_INSUFFICIENT", debate_round=3)
        assert route_after_judge(state) == "finalize_node"


class TestDebugRouter:
    def test_success_goes_to_finalize(self):
        state = _state(debug_decision="SUCCESS")
        assert route_after_debug(state) == "finalize_node"

    def test_doc_research_within_rounds(self):
        state = _state(debug_decision="DOC_RESEARCH_REQUIRED", debug_round=1)
        assert route_after_debug(state) == "debug_research_node"

    def test_doc_research_at_max_rounds_goes_to_finalize(self):
        state = _state(debug_decision="DOC_RESEARCH_REQUIRED", debug_round=3)
        assert route_after_debug(state) == "finalize_node"

    def test_patch_required_within_rounds(self):
        state = _state(debug_decision="PATCH_REQUIRED", debug_round=0)
        assert route_after_debug(state) == "debugger_node"

    def test_blocked_goes_to_finalize(self):
        state = _state(debug_decision="BLOCKED")
        assert route_after_debug(state) == "finalize_node"
