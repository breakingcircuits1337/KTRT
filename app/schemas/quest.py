from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ProviderMap(BaseModel):
    """Optional per-role model overrides."""
    researcher: str | None = None
    evidence: str | None = None
    planner: str | None = None
    critic: str | None = None
    judge: str | None = None
    builder: str | None = None
    debugger: str | None = None


class QuestRequest(BaseModel):
    query: str = Field(..., description="The research question or build task.")
    mode: Literal["research", "build"] = Field(
        default="research",
        description="'research' returns a final answer; 'build' produces code artifacts.",
    )
    max_debate_rounds: int = Field(default=3, ge=1, le=5)
    max_debug_rounds: int = Field(default=3, ge=0, le=5)
    include_sources: bool = Field(default=True)
    providers: ProviderMap = Field(default_factory=ProviderMap)


class DebugSummary(BaseModel):
    rounds: int
    decision: str | None = None
    known_issues: list[str] = Field(default_factory=list)


class DebateSummary(BaseModel):
    rounds: int
    judge_decision: str | None = None
    key_critiques: list[str] = Field(default_factory=list)


class ArtifactOut(BaseModel):
    path: str
    artifact_type: str


class SourceOut(BaseModel):
    title: str
    url: str
    snippet: str | None = None
    published_at: str | None = None
    source_type: str | None = None
    credibility: float | None = None


class QuestResponse(BaseModel):
    run_id: str
    status: str
    theme: str = "Merlin's Knights of the Round Table"
    final_answer: str
    confidence: float | None = None
    debate_summary: DebateSummary
    debug_summary: DebugSummary
    artifacts: list[ArtifactOut] = Field(default_factory=list)
    sources: list[SourceOut] = Field(default_factory=list)
    model_trace: list[dict[str, Any]] = Field(default_factory=list)
