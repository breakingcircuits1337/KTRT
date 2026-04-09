from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.quest import QuestRequest, QuestResponse, ProviderMap
from app.graph.state import MerlinState, SourceItem, CritiqueItem, ClaimItem


def test_quest_request_defaults():
    req = QuestRequest(query="What is LangGraph?")
    assert req.mode == "research"
    assert req.max_debate_rounds == 3
    assert req.max_debug_rounds == 2
    assert req.include_sources is True


def test_quest_request_with_providers():
    req = QuestRequest(
        query="Build a REST API",
        mode="build",
        providers=ProviderMap(researcher="mistral-large-latest", builder="claude-sonnet-4-6"),
    )
    assert req.providers.researcher == "mistral-large-latest"
    assert req.mode == "build"


def test_quest_request_validation():
    with pytest.raises(ValidationError):
        QuestRequest(query="test", max_debate_rounds=0)  # ge=1


def test_merlin_state_defaults():
    state = MerlinState(query="test query", run_id="quest_abc123")
    assert state.run_status == "running"
    assert state.debate_round == 0
    assert state.sources == []
    assert state.critiques == []


def test_source_item():
    s = SourceItem(title="Docs", url="https://example.com", snippet="some text")
    assert s.credibility is None
    assert s.source_type is None


def test_critique_item():
    c = CritiqueItem(issue="Missing tests", severity="high", recommendation="Add pytest coverage")
    assert c.severity == "high"


def test_claim_item():
    from app.utils.ids import make_claim_id
    cid = make_claim_id()
    assert cid.startswith("claim_")
    claim = ClaimItem(claim_id=cid, text="Python is fast", support_status="weak")
    assert claim.support_status == "weak"
