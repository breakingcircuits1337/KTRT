from __future__ import annotations

import json
import time
from typing import AsyncIterator

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

# Graph node → (knight, role) for progress display.
KNIGHT_BY_NODE: dict[str, tuple[str, str]] = {
    "research_node": ("Sir Bedivere", "Researcher"),
    "evidence_node": ("Sir Percival", "Evidence"),
    "planner_node": ("Sir Lancelot", "Planner"),
    "debate_node": ("The Round Table", "Debate"),
    "judge_node": ("The Crown", "Judge"),
    "builder_node": ("Sir Kay", "Builder"),
    "debugger_node": ("Sir Bors", "Debugger"),
    "debug_research_node": ("Sir Bedivere", "Targeted Research"),
    "finalize_node": ("The Chronicle", "Finalizer"),
}


def _prepare(request: QuestRequest) -> tuple[str, MerlinState]:
    run_id = make_run_id("quest")
    logger.info("quest_start", run_id=run_id, query=request.query[:100], mode=request.mode)
    providers = {
        k: v for k, v in request.providers.model_dump().items() if v is not None
    }
    initial_state = MerlinState(
        run_id=run_id,
        query=request.query,
        mode=request.mode,
        max_debate_rounds=request.max_debate_rounds,
        max_debug_rounds=request.max_debug_rounds,
        providers=providers,
    )
    return run_id, initial_state


def _build_response(
    run_id: str, request: QuestRequest, last_state: dict, timed_out: bool
) -> QuestResponse:
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
        f"[{c.severity.upper()}] {c.issue[:120]}" for c in (final_state.critiques or [])
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


async def run_quest(request: QuestRequest) -> QuestResponse:
    """Run a quest to completion (or the time budget) and return the result."""
    run_id, initial_state = _prepare(request)
    graph = get_graph()

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

    return _build_response(run_id, request, last_state, timed_out)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def run_quest_stream(request: QuestRequest) -> AsyncIterator[str]:
    """Run a quest and stream Server-Sent Events: a `node` event as each knight
    finishes, then a final `result` event carrying the full QuestResponse."""
    run_id, initial_state = _prepare(request)
    graph = get_graph()

    deadline = time.monotonic() + settings.total_workflow_timeout
    last_state: dict = {}
    timed_out = False

    yield _sse("start", {"run_id": run_id, "mode": request.mode})

    # stream_mode as a list yields (mode, chunk) tuples: "updates" tells us which
    # node just ran; "values" carries the full accumulated state.
    stream = graph.astream(initial_state, stream_mode=["updates", "values"])
    try:
        async for mode, chunk in stream:
            if mode == "updates":
                for node_name in chunk:
                    knight, role = KNIGHT_BY_NODE.get(node_name, (node_name, ""))
                    yield _sse("node", {"node": node_name, "knight": knight, "role": role})
            elif mode == "values":
                last_state = chunk
                if time.monotonic() >= deadline:
                    timed_out = True
                    logger.error("quest_timeout", run_id=run_id)
                    yield _sse("timeout", {"run_id": run_id})
                    break
    except Exception as exc:  # surface failures to the client instead of hanging
        logger.error("quest_stream_error", run_id=run_id, error=str(exc))
        yield _sse("error", {"message": str(exc)[:300]})
        return
    finally:
        await stream.aclose()

    response = _build_response(run_id, request, last_state, timed_out)
    yield _sse("result", response.model_dump(mode="json"))
