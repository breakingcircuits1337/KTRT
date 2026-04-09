from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

JudgeDecision = Literal[
    "APPROVED",
    "REVISION_REQUIRED",
    "EVIDENCE_INSUFFICIENT",
    "CONTRADICTION_FOUND",
]

DebugDecision = Literal[
    "SUCCESS",
    "PATCH_REQUIRED",
    "DOC_RESEARCH_REQUIRED",
    "BLOCKED",
]


class SourceItem(BaseModel):
    title: str
    url: str
    snippet: str | None = None
    published_at: str | None = None
    source_type: str | None = None
    credibility: float | None = None


class ClaimItem(BaseModel):
    claim_id: str
    text: str
    support_status: Literal["supported", "weak", "unsupported", "contradicted"]
    evidence_refs: list[str] = Field(default_factory=list)
    notes: str = ""


class CritiqueItem(BaseModel):
    issue: str
    severity: Literal["low", "medium", "high"]
    recommendation: str


class ArtifactItem(BaseModel):
    path: str
    content: str
    artifact_type: Literal["code", "config", "test", "doc"]


class MerlinState(BaseModel):
    # Core query
    query: str
    objective: str = ""
    mode: Literal["research", "build"] = "research"

    # Provider overrides (role -> model_id)
    providers: dict[str, str] = Field(default_factory=dict)

    # Workflow state
    research_notes: str = ""
    evidence_report: str = ""
    implementation_plan: str = ""
    draft_answer: str = ""
    draft_code_summary: str = ""
    debug_notes: str = ""
    final_answer: str = ""

    # Collections
    sources: list[SourceItem] = Field(default_factory=list)
    claims: list[ClaimItem] = Field(default_factory=list)
    critiques: list[CritiqueItem] = Field(default_factory=list)
    artifacts: list[ArtifactItem] = Field(default_factory=list)

    # Routing decisions
    judge_decision: JudgeDecision | None = None
    debug_decision: DebugDecision | None = None

    # Loop counters
    debate_round: int = 0
    max_debate_rounds: int = 3
    debug_round: int = 0
    max_debug_rounds: int = 3

    # Run metadata
    run_id: str = ""
    run_status: Literal["running", "complete", "blocked", "failed"] = "running"
    confidence: float | None = None
    model_trace: list[dict[str, Any]] = Field(default_factory=list)
