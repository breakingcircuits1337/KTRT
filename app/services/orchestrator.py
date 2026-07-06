from __future__ import annotations

import time

from app.config import settings
from app.graph.state import MerlinState
from app.graph.workflow import get_graph
from app.schemas.quest import (
    ArtifactOut,
    DebateSummary,
    DebugSummary,
    QuestRequest,
    QuestResponse,
    SourceOut,
)
from app.utils.ids import make_run_id
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def run_quest(request: QuestRequest) -> QuestResponse:
    run_id = make_run_id("quest")
    logger.info("quest_start", run_id=run_id, query=request.query[:100], mode=request.mode)

    providers = {
        k: v
        for k, v in request.providers.model_dump().items()
        if v is not None
    }

    initial_state = MerlinState(
        run_id=run_id,
        query=request.query,
        mode=request.mode,
        max_debate_rounds=request.max_debate_rounds,
        max_debug_rounds=request.max_debug_rounds,
        providers=providers,
    )

    graph = get_graph()

    # Stream the graph with a wall-clock budget, keeping the latest state after
    # every super-step. If the budget is exhausted before the workflow finishes
    # (slow reasoning models can make each debate/revision cycle 1-2 minutes),
    # stop after the current node and finalize gracefully with the best draft so
    # far — rather than hard-cancelling and discarding all the work.
    deadline = time.monotonic() + settings.total_workflow_timeout
    last_state: dict = {}
    timed_out = False
    stream = graph.astream(initial_state, stream_mode="values")
    try:
        async for chunk in stream:
            last_state = chunk
            if time.monotonic() >= deadline:
                timed_out = True
                logger.error("quest_timeout", run_id=run_id)
                break
    finally:
        await stream.aclose()

    if not last_state:
        return QuestResponse(
            run_id=run_id,
            status="failed",
            final_answer="The quest produced no result.",
            confidence=None,
            debate_summary=DebateSummary(rounds=0),
            debug_summary=DebugSummary(rounds=0),
        )

    # LangGraph (>=1.x) yields the graph state as a plain dict even when the
    # state schema is a pydantic model — rehydrate it so attribute access works.
    final_state = MerlinState(**last_state) if isinstance(last_state, dict) else last_state

    # Resolve the answer/status, salvaging a partial draft on timeout.
    resolved_status = final_state.run_status
    resolved_answer = final_state.final_answer or final_state.draft_answer
    if timed_out and resolved_status not in ("complete", "blocked"):
        resolved_status = "partial"
        best = (
            final_state.final_answer
            or final_state.draft_answer
            or final_state.implementation_plan
            or final_state.evidence_report
            or final_state.research_notes
            or "The knights ran out of time before producing an answer."
        )
        resolved_answer = (
            "_This quest reached its time budget before the Round Table "
            "finished. Below is the best draft produced so far._\n\n" + best
        )

    logger.info(
        "quest_complete",
        run_id=run_id,
        status=resolved_status,
        timed_out=timed_out,
        debate_rounds=final_state.debate_round,
        debug_rounds=final_state.debug_round,
    )

    key_critiques = [
        f"[{c.severity.upper()}] {c.issue[:120]}"
        for c in (final_state.critiques or [])
    ]
    debug_issues = []
    if final_state.debug_notes and final_state.debug_decision == "BLOCKED":
        debug_issues = ["Blocked: see debug_notes in model trace."]

    sources_out = []
    if request.include_sources:
        sources_out = [
            SourceOut(
                title=s.title,
                url=s.url,
                snippet=s.snippet,
                published_at=s.published_at,
                source_type=s.source_type,
                credibility=s.credibility,
            )
            for s in final_state.sources
        ]

    return QuestResponse(
        run_id=run_id,
        status=resolved_status,
        final_answer=resolved_answer,
        confidence=final_state.confidence,
        debate_summary=DebateSummary(
            rounds=final_state.debate_round,
            judge_decision=final_state.judge_decision,
            key_critiques=key_critiques,
        ),
        debug_summary=DebugSummary(
            rounds=final_state.debug_round,
            decision=final_state.debug_decision,
            known_issues=debug_issues,
        ),
        artifacts=[
            ArtifactOut(path=a.path, artifact_type=a.artifact_type)
            for a in final_state.artifacts
        ],
        sources=sources_out,
        model_trace=final_state.model_trace,
    )
