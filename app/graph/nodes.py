from __future__ import annotations

import json
import re
from typing import Any

from app.graph.state import (
    ArtifactItem,
    ClaimItem,
    CritiqueItem,
    DebugDecision,
    JudgeDecision,
    MerlinState,
    SourceItem,
)
from app.graph import prompts
from app.providers.registry import get_role_adapter
from app.research.search import search
from app.research.rank import rank_sources
from app.utils.ids import make_claim_id
from app.utils.logging import get_logger

logger = get_logger(__name__)

ROLE_LABELS = {
    "research_node": "Sir Bedivere",
    "evidence_node": "Sir Percival",
    "planner_node": "Sir Lancelot",
    "debate_node": "Round Table",
    "judge_node": "The Crown",
    "builder_node": "Sir Kay",
    "debugger_node": "Sir Bors",
    "debug_research_node": "Sir Bedivere (Debug)",
    "finalize_node": "The Chronicle",
}


def _trace(state: MerlinState, node: str, model: str, tokens_in: int, tokens_out: int, latency_ms: float) -> list[dict[str, Any]]:
    entry = {
        "node": node,
        "knight": ROLE_LABELS.get(node, node),
        "model": model,
        "prompt_tokens": tokens_in,
        "completion_tokens": tokens_out,
        "latency_ms": round(latency_ms, 1),
    }
    return state.model_trace + [entry]


def _extract_json(text: str) -> dict:
    """Extract first complete JSON object from LLM output using incremental decoding.

    Unlike a greedy regex this correctly handles nested braces and stops at the
    exact end of the first valid object rather than the last closing brace in the
    text.
    """
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch == "{":
            try:
                obj, _ = decoder.raw_decode(text, i)
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                continue
    logger.debug("No valid JSON object found in LLM output", snippet=text[:200])
    return {}


async def research_node(state: MerlinState) -> dict:
    """Sir Bedivere — web research and source retrieval."""
    logger.info("research_node start", run_id=state.run_id)

    raw_results = await search(state.query)
    ranked_sources = rank_sources(raw_results)

    source_text = "\n".join(
        f"- [{s.title}]({s.url})\n  {s.snippet or ''}" for s in ranked_sources
    )
    user_prompt = (
        f"Query: {state.query}\n\n"
        f"Sources retrieved:\n{source_text}\n\n"
        "Produce a Research Brief based on these sources."
    )

    adapter = get_role_adapter("researcher", state.providers.get("researcher"))
    text, trace = await adapter.generate(
        system=prompts.RESEARCHER,
        user=user_prompt,
        temperature=0.1,
    )

    existing_sources = list(state.sources)
    urls_seen = {s.url for s in existing_sources}
    new_sources = [s for s in ranked_sources if s.url not in urls_seen]

    return {
        "research_notes": text,
        "sources": existing_sources + new_sources,
        "model_trace": _trace(state, "research_node", trace.model, trace.prompt_tokens, trace.completion_tokens, trace.latency_ms),
    }


async def evidence_node(state: MerlinState) -> dict:
    """Sir Percival — convert research notes into structured evidence report."""
    logger.info("evidence_node start", run_id=state.run_id)

    user_prompt = (
        f"Research Notes:\n{state.research_notes}\n\n"
        f"Sources:\n"
        + "\n".join(f"- [{s.title}]({s.url})" for s in state.sources)
        + "\n\nProduce a structured Evidence Report with Claims Inventory."
    )

    adapter = get_role_adapter("evidence", state.providers.get("evidence"))
    text, trace = await adapter.generate(
        system=prompts.EVIDENCE_BUILDER,
        user=user_prompt,
        temperature=0.15,
    )

    # Extract simple claims from the report
    claims = list(state.claims)
    lines = [l.strip() for l in text.split("\n") if l.strip().startswith("|")]
    for line in lines[1:]:  # skip header row
        parts = [p.strip() for p in line.split("|") if p.strip()]
        # Skip markdown separator rows (e.g. | --- | --- | --- |)
        if not parts or all(set(p) <= {"-", ":"} for p in parts):
            continue
        if len(parts) >= 2:
            status_map = {
                "supported": "supported",
                "weak": "weak",
                "unsupported": "unsupported",
                "contradicted": "contradicted",
            }
            raw_status = parts[1].lower() if len(parts) > 1 else "weak"
            status = status_map.get(raw_status, "weak")
            claims.append(
                ClaimItem(
                    claim_id=make_claim_id(),
                    text=parts[0],
                    support_status=status,
                    notes=parts[2] if len(parts) > 2 else "",
                )
            )

    return {
        "evidence_report": text,
        "claims": claims,
        "model_trace": _trace(state, "evidence_node", trace.model, trace.prompt_tokens, trace.completion_tokens, trace.latency_ms),
    }


async def planner_node(state: MerlinState) -> dict:
    """Sir Lancelot — build implementation plan from evidence."""
    logger.info("planner_node start", run_id=state.run_id)

    critique_text = ""
    if state.critiques:
        critique_text = "\n\nPrevious critiques to address:\n" + "\n".join(
            f"- [{c.severity.upper()}] {c.issue} → {c.recommendation}"
            for c in state.critiques
        )

    user_prompt = (
        f"Query: {state.query}\n\n"
        f"Evidence Report:\n{state.evidence_report}"
        + critique_text
        + "\n\nProduce a concrete Implementation Plan."
    )

    adapter = get_role_adapter("planner", state.providers.get("planner"))
    text, trace = await adapter.generate(
        system=prompts.PLANNER,
        user=user_prompt,
        temperature=0.2,
    )

    return {
        "implementation_plan": text,
        "draft_answer": text,
        "model_trace": _trace(state, "planner_node", trace.model, trace.prompt_tokens, trace.completion_tokens, trace.latency_ms),
    }


async def debate_node(state: MerlinState) -> dict:
    """Round Table — adversarial critique of the current plan."""
    logger.info("debate_node start", run_id=state.run_id, round=state.debate_round)

    user_prompt = (
        f"Query: {state.query}\n\n"
        f"Implementation Plan:\n{state.implementation_plan}\n\n"
        f"Evidence Report:\n{state.evidence_report}\n\n"
        "Critique this plan aggressively. Return structured critique items."
    )

    adapter = get_role_adapter("critic", state.providers.get("critic"))
    text, trace = await adapter.generate(
        system=prompts.CRITIC,
        user=user_prompt,
        temperature=0.3,
    )

    # Parse critique items from structured output
    critiques = []
    current: dict = {}
    for line in text.split("\n"):
        line = line.strip()
        if line.upper().startswith("- ISSUE:") or line.upper().startswith("ISSUE:"):
            if current.get("issue"):
                critiques.append(current)
            current = {"issue": re.sub(r"^[-•]?\s*(ISSUE:)\s*", "", line, flags=re.IGNORECASE).strip()}
        elif line.upper().startswith("SEVERITY:"):
            raw = re.sub(r"SEVERITY:\s*", "", line, flags=re.IGNORECASE).strip().lower()
            current["severity"] = raw if raw in ("low", "medium", "high") else "medium"
        elif line.upper().startswith("RECOMMENDATION:"):
            current["recommendation"] = re.sub(r"RECOMMENDATION:\s*", "", line, flags=re.IGNORECASE).strip()
    if current.get("issue"):
        critiques.append(current)

    critique_items = [
        CritiqueItem(
            issue=c.get("issue", ""),
            severity=c.get("severity", "medium"),
            recommendation=c.get("recommendation", ""),
        )
        for c in critiques
        if c.get("issue")
    ]

    if not critique_items:
        logger.warning(
            "debate_node failed to parse structured critiques; falling back to raw text",
            run_id=state.run_id,
            round=state.debate_round,
            raw_snippet=text[:200],
        )
        critique_items = [CritiqueItem(issue=text[:500], severity="medium", recommendation="See full critique above.")]

    return {
        "critiques": critique_items,
        "debate_round": state.debate_round + 1,
        "model_trace": _trace(state, "debate_node", trace.model, trace.prompt_tokens, trace.completion_tokens, trace.latency_ms),
    }


async def judge_node(state: MerlinState) -> dict:
    """The Crown — evaluate plan and critiques, make routing decision."""
    logger.info("judge_node start", run_id=state.run_id)

    critique_text = "\n".join(
        f"[{c.severity.upper()}] {c.issue} → {c.recommendation}"
        for c in state.critiques
    )
    claims_text = "\n".join(
        f"- {cl.text} ({cl.support_status})" for cl in state.claims
    )

    user_prompt = (
        f"Query: {state.query}\n\n"
        f"Implementation Plan:\n{state.implementation_plan}\n\n"
        f"Claims:\n{claims_text}\n\n"
        f"Critiques:\n{critique_text}\n\n"
        "Make a routing decision. Return JSON."
    )

    adapter = get_role_adapter("judge", state.providers.get("judge"))
    text, trace = await adapter.generate(
        system=prompts.MODERATOR,
        user=user_prompt,
        temperature=0.1,
    )

    parsed = _extract_json(text)
    raw_decision = parsed.get("decision", "APPROVED").upper()
    valid_decisions: set[JudgeDecision] = {"APPROVED", "REVISION_REQUIRED", "EVIDENCE_INSUFFICIENT", "CONTRADICTION_FOUND"}
    judge_decision: JudgeDecision = raw_decision if raw_decision in valid_decisions else "APPROVED"
    try:
        confidence = float(parsed.get("confidence", 0.7))
        confidence = max(0.0, min(1.0, confidence))
    except (TypeError, ValueError):
        confidence = 0.7

    return {
        "judge_decision": judge_decision,
        "confidence": confidence,
        "model_trace": _trace(state, "judge_node", trace.model, trace.prompt_tokens, trace.completion_tokens, trace.latency_ms),
    }


async def builder_node(state: MerlinState) -> dict:
    """Sir Kay — implement the approved plan."""
    logger.info("builder_node start", run_id=state.run_id)

    user_prompt = (
        f"Query: {state.query}\n\n"
        f"Approved Plan:\n{state.implementation_plan}\n\n"
        f"Evidence Report:\n{state.evidence_report}\n\n"
        "Implement the approved plan. Produce all artifacts."
    )

    adapter = get_role_adapter("builder", state.providers.get("builder"))
    text, trace = await adapter.generate(
        system=prompts.BUILDER,
        user=user_prompt,
        temperature=0.1,
        max_tokens=8192,
    )

    # Extract artifacts from markdown code blocks.
    # Primary strategy: look for "### Artifact: <path>" immediately before a fenced block.
    # Fallback: pair remaining fenced blocks with generated names.
    artifacts = list(state.artifacts)
    paired_pattern = re.compile(
        r"###\s+Artifact:\s*(.+?)\n```(\w+)?\n(.*?)```",
        re.DOTALL | re.IGNORECASE,
    )
    orphan_pattern = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)

    paired_spans: set[int] = set()
    for m in paired_pattern.finditer(text):
        path = m.group(1).strip()
        lang = (m.group(2) or "").lower()
        content = m.group(3).strip()
        ext = lang
        artifact_type = (
            "test" if "test" in path.lower() else
            "config" if ext in ("yaml", "toml", "json", "env") else
            "doc" if ext in ("md", "rst", "txt") else
            "code"
        )
        artifacts.append(ArtifactItem(path=path, content=content, artifact_type=artifact_type))
        paired_spans.update(range(m.start(), m.end()))

    # Capture any fenced blocks not already covered by a paired match
    fallback_index = 0
    for m in orphan_pattern.finditer(text):
        if m.start() in paired_spans:
            continue
        lang = (m.group(1) or "").lower()
        content = m.group(2).strip()
        if not content:
            continue
        ext = lang
        path = f"artifact_{fallback_index}.{ext or 'txt'}"
        artifact_type = (
            "config" if ext in ("yaml", "toml", "json", "env") else
            "doc" if ext in ("md", "rst", "txt") else
            "code"
        )
        artifacts.append(ArtifactItem(path=path, content=content, artifact_type=artifact_type))
        fallback_index += 1

    return {
        "artifacts": artifacts,
        "draft_code_summary": text,
        "model_trace": _trace(state, "builder_node", trace.model, trace.prompt_tokens, trace.completion_tokens, trace.latency_ms),
    }


async def debugger_node(state: MerlinState) -> dict:
    """Sir Bors — diagnose failures and classify debug decision."""
    logger.info("debugger_node start", run_id=state.run_id, round=state.debug_round)

    artifacts_text = "\n\n".join(
        f"### {a.path}\n```\n{a.content[:1000]}\n```" for a in state.artifacts[:5]
    )
    user_prompt = (
        f"Query: {state.query}\n\n"
        f"Implementation Plan:\n{state.implementation_plan}\n\n"
        f"Artifacts:\n{artifacts_text}\n\n"
        f"Previous Debug Notes:\n{state.debug_notes}\n\n"
        "Diagnose any issues and return a JSON debug decision."
    )

    adapter = get_role_adapter("debugger", state.providers.get("debugger"))
    text, trace = await adapter.generate(
        system=prompts.DEBUGGER,
        user=user_prompt,
        temperature=0.1,
    )

    parsed = _extract_json(text)
    raw_dd = parsed.get("debug_decision", "SUCCESS").upper()
    valid_dd: set[DebugDecision] = {"SUCCESS", "PATCH_REQUIRED", "DOC_RESEARCH_REQUIRED", "BLOCKED"}
    debug_decision: DebugDecision = raw_dd if raw_dd in valid_dd else "SUCCESS"

    debug_notes = state.debug_notes
    if parsed.get("root_cause"):
        debug_notes += f"\n\nRound {state.debug_round + 1} — Root cause: {parsed['root_cause']}"
    if parsed.get("patch_notes"):
        debug_notes += f"\nPatch: {parsed['patch_notes']}"
    if parsed.get("research_query"):
        debug_notes += f"\nresearch_query: {parsed['research_query']}"

    return {
        "debug_notes": debug_notes,
        "debug_decision": debug_decision,
        "debug_round": state.debug_round + 1,
        "model_trace": _trace(state, "debugger_node", trace.model, trace.prompt_tokens, trace.completion_tokens, trace.latency_ms),
    }


async def debug_research_node(state: MerlinState) -> dict:
    """Sir Bedivere (targeted) — search for solutions to specific failures."""
    logger.info("debug_research_node start", run_id=state.run_id)

    search_query = state.debug_notes.split("research_query:")[-1].strip()[:200] if "research_query:" in state.debug_notes else state.query + " error fix"
    raw_results = await search(search_query, max_results=5)
    ranked = rank_sources(raw_results)

    source_text = "\n".join(
        f"- [{s.title}]({s.url})\n  {s.snippet or ''}" for s in ranked
    )
    user_prompt = (
        f"Debug context:\n{state.debug_notes}\n\n"
        f"Targeted sources:\n{source_text}\n\n"
        "Produce targeted debug research findings."
    )

    adapter = get_role_adapter("researcher", state.providers.get("researcher"))
    text, trace = await adapter.generate(
        system=prompts.TARGETED_RESEARCHER,
        user=user_prompt,
        temperature=0.1,
    )

    existing = list(state.sources)
    seen = {s.url for s in existing}
    new_sources = [s for s in ranked if s.url not in seen]

    return {
        "research_notes": state.research_notes + "\n\n## Debug Research\n" + text,
        "sources": existing + new_sources,
        "model_trace": _trace(state, "debug_research_node", trace.model, trace.prompt_tokens, trace.completion_tokens, trace.latency_ms),
    }


async def finalize_node(state: MerlinState) -> dict:
    """The Chronicle — assemble the final deliverable."""
    logger.info("finalize_node start", run_id=state.run_id)

    sources_text = "\n".join(
        f"- [{s.title}]({s.url})" for s in state.sources[:10]
    )
    artifacts_summary = "\n".join(
        f"- {a.path} ({a.artifact_type})" for a in state.artifacts
    )
    user_prompt = (
        f"Query: {state.query}\n\n"
        f"Implementation Plan:\n{state.implementation_plan}\n\n"
        f"Evidence Report:\n{state.evidence_report}\n\n"
        f"Debug Notes:\n{state.debug_notes}\n\n"
        f"Artifacts produced:\n{artifacts_summary}\n\n"
        f"Sources:\n{sources_text}\n\n"
        f"Judge Decision: {state.judge_decision}\n\n"
        "Assemble the final deliverable."
    )

    adapter = get_role_adapter("planner", state.providers.get("planner"))
    text, trace = await adapter.generate(
        system=prompts.FINALIZER,
        user=user_prompt,
        temperature=0.15,
        max_tokens=4096,
    )

    run_status = "blocked" if state.debug_decision == "BLOCKED" else "complete"

    return {
        "final_answer": text,
        "run_status": run_status,
        "model_trace": _trace(state, "finalize_node", trace.model, trace.prompt_tokens, trace.completion_tokens, trace.latency_ms),
    }
