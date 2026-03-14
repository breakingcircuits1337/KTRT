# Multi-Model Research Lab MCP Blueprint

## Objective
Build an MCP-compatible orchestration service that connects Azure OpenAI, Claude, Gemini, Groq, and Mistral into a single adversarial research workflow. The service exposes a stable API for GPT Actions / Create App integrations, performs web research, runs structured debate rounds, and returns a final consensus answer with citations, critiques, and confidence notes.

## Core Design

### High-level components
1. **Client Layer**
   - OpenAI GPT Action / Create App front end
   - Sends one request per user query
   - Receives a finalized consensus response

2. **MCP / Orchestration API**
   - FastAPI service
   - Authenticates requests
   - Accepts a research task
   - Manages workflow state
   - Returns structured output

3. **Agent Graph Runtime**
   - LangGraph preferred for cyclical debate loops
   - Explicit nodes for research, synthesis, critique, moderation, revision, finalize

4. **Provider Adapters**
   - Azure OpenAI
   - Anthropic Claude
   - Google Gemini
   - Groq
   - Mistral
   - Each adapter normalizes request/response handling, token limits, retries, and errors

5. **Research Layer**
   - Tavily / Exa / Brave Search
   - Fetches sources
   - Extracts snippets, titles, URLs, timestamps
   - Optional reranking and deduplication

6. **Memory / Persistence**
   - Redis for short-lived run state and cache
   - Postgres for run logs, outputs, source manifests, evaluation records

7. **Observability**
   - Structured logs
   - Traces per workflow node
   - Token/accounting metrics
   - Per-model latency and error rates

---

## Recommended Stack

### API / orchestration
- Python 3.11+
- FastAPI
- Uvicorn / Gunicorn
- Pydantic v2
- httpx
- LangGraph
- tenacity

### Storage / infra
- Redis
- Postgres
- Docker Compose for local dev
- Optional: Celery or Dramatiq only if you later need detached runs

### Research
- Tavily or Exa for search
- Trafilatura / readability-lxml for page extraction if you crawl result pages

### Security
- API key auth for inbound GPT requests
- Secrets in environment or vault
- Per-provider rate limiting

---

## Debate Workflow

### Revised conceptual pipeline
This is not a search engine. It is a **research-and-build lab** with explicit role separation:

```text
User Query
   -> Researcher (web research)
   -> Evidence Builder (research synthesis and report)
   -> Conceptualizer / Planner (solution framing and plan)
   -> Debate Panel (adversarial improvement loop)
   -> Code Writer / Builder (implementation)
   -> Debugger (including targeted web research for hard failures)
   -> Finalizer
```

### State object
```python
from typing import Any, Literal
from pydantic import BaseModel, Field

class SourceItem(BaseModel):
    title: str
    url: str
    snippet: str | None = None
    published_at: str | None = None
    credibility: float | None = None

class CritiqueItem(BaseModel):
    issue: str
    severity: Literal["low", "medium", "high"]
    recommendation: str

class DebateState(BaseModel):
    query: str
    research_brief: str = ""
    evidence_report: str = ""
    implementation_plan: str = ""
    sources: list[SourceItem] = Field(default_factory=list)
    draft_answer: str = ""
    draft_code: str = ""
    critiques: list[CritiqueItem] = Field(default_factory=list)
    moderator_decision: Literal["revise", "finalize"] | None = None
    revision_count: int = 0
    max_revisions: int = 3
    debug_notes: str = ""
    final_answer: str = ""
    confidence: float | None = None
    model_trace: list[dict[str, Any]] = Field(default_factory=list)
```

### Agent roles

#### 1. Researcher
**Primary role:** targeted web research and source retrieval

Task:
- expand the user query into research questions
- perform deep web research
- identify authoritative and current sources
- collect source snippets and unresolved questions

Suggested model pairing:
- Mistral or Gemini Flash for retrieval-oriented compression
- Tavily / Exa / Brave Search for external research

Output:
- source manifest
- raw research notes
- unresolved factual gaps

#### 2. Evidence Builder
**Primary role:** convert raw research into a structured report

Task:
- synthesize findings into a coherent evidence brief
- separate verified facts, claims, assumptions, and open questions
- produce a report that later nodes can reason over efficiently

Output:
- evidence report
- claim inventory
- citation mapping

#### 3. Conceptualizer / Planner
**Primary role:** transform the evidence report into a concrete solution strategy

Task:
- define the problem clearly
- choose architecture or answer structure
- identify tradeoffs, constraints, dependencies, and milestones
- prepare a build plan before debate begins

Suggested model pairing:
- Claude or Gemini Pro-class model

Output:
- implementation plan
- assumptions list
- risk register

#### 4. Debate Panel
**Primary role:** adversarial improvement of the plan or answer

This is where **ReConcile / SocraSynth-style round-table debate** fits.

Suggested debate protocol:
- Round 1: each role reviews the plan independently
- Round 2: critic/adversary attacks weak claims, hidden assumptions, missing evidence, architecture flaws
- Round 3: planner/synthesizer revises the plan
- Moderator decides whether another round is needed or the plan is robust enough for execution

Suggested model assignments:
- Synthesizer / reviser: Claude
- Adversary / red team: Azure OpenAI or Groq-hosted Llama
- Moderator: Gemini
- Optional secondary critic: Mistral

Output:
- critique set
- revised plan
- approval / revision decision

#### 5. Code Writer / Builder
**Primary role:** implement the approved plan

Task:
- generate code, config, tests, and wiring
- follow the approved architecture instead of improvising from scratch
- produce implementation artifacts in bounded units

Suggested model pairing:
- Claude, Azure OpenAI, or Groq depending on language and latency needs

Output:
- code artifacts
- test scaffold
- implementation notes

#### 6. Debugger
**Primary role:** fix failures and hard edge cases

Task:
- inspect runtime/test/lint failures
- reason about root cause
- for hard or unfamiliar issues, perform targeted web research against official docs, issue trackers, and known error reports
- patch the implementation and re-test

Suggested model pairing:
- Azure OpenAI or Claude for debugging
- Mistral / Gemini Flash for rapid error summarization

Output:
- debug report
- patch set
- remaining known issues

#### 7. Finalizer
**Primary role:** assemble the final deliverable

Task:
- return the final answer, design, code, and caveats
- include sources used during research and debugging
- include confidence and residual risks

---

## LangGraph Layout

### Node sequence
```text
START
  -> research
  -> evidence_builder
  -> conceptualize
  -> debate
      -> if revise: conceptualize -> debate
      -> if approved: build
  -> debug
      -> if unresolved hard problem: targeted_research -> debug
      -> else: finalize
  -> END
```

### Routing rule
- Stop when moderator says `finalize`
- Stop when `revision_count >= max_revisions`
- Optional stop when critique severity falls below threshold

---

## FastAPI Surface

### Primary endpoint
`POST /v1/debate`

Request:
```json
{
  "query": "Explain the likely economic effects of X over the next 12 months",
  "max_revisions": 2,
  "depth": "deep",
  "include_sources": true,
  "models": {
    "researcher": "mistral-large-latest",
    "synthesizer": "claude-3-7-sonnet",
    "adversary": "azure:gpt-4.1",
    "moderator": "gemini-2.0-flash"
  }
}
```

Response:
```json
{
  "answer": "...",
  "confidence": 0.84,
  "decision": "finalize",
  "sources": [
    {
      "title": "...",
      "url": "https://...",
      "published_at": "2026-03-01"
    }
  ],
  "debate_summary": {
    "rounds": 2,
    "key_critiques": [
      "Claim X lacked direct support and was narrowed.",
      "Counterargument Y was added."
    ]
  }
}
```

### Support endpoints
- `GET /healthz`
- `GET /openapi.json`
- `POST /v1/models/test`
- `POST /v1/search`
- `GET /v1/runs/{run_id}`

---

## OpenAPI / GPT Action Strategy

### Why a single action is better
The GPT side should call one stable backend action instead of attempting multi-provider fanout itself. This avoids:
- context window fragmentation
- frontend tool timeout failures
- exposing provider credentials in the GPT configuration
- brittle prompt-level orchestration

### GPT / Create App instructions
Use a single action, for example:
- `initiate_debate`

Minimal instruction policy:
> You are the front-end interface for a multi-model research lab. For any substantive question, call `initiate_debate`. Do not answer from internal knowledge when the tool is available. Present the returned consensus answer clearly, preserving source links, confidence notes, and caveats.

---

## Provider Adapter Pattern

Create a thin abstraction layer so each model provider implements the same interface.

```python
from abc import ABC, abstractmethod

class LLMAdapter(ABC):
    @abstractmethod
    async def generate(self, system: str, user: str, temperature: float = 0.2) -> str:
        raise NotImplementedError
```

Implementations:
- `AzureOpenAIAdapter`
- `AnthropicAdapter`
- `GeminiAdapter`
- `GroqAdapter`
- `MistralAdapter`

Each adapter should standardize:
- retries
- timeout
- max tokens
- provider-specific response extraction
- structured error objects

---

## Minimal Project Layout

```text
research-lab-mcp/
├─ app/
│  ├─ main.py
│  ├─ config.py
│  ├─ api/
│  │  ├─ routes_debate.py
│  │  └─ routes_health.py
│  ├─ schemas/
│  │  ├─ debate.py
│  │  └─ common.py
│  ├─ graph/
│  │  ├─ state.py
│  │  ├─ nodes.py
│  │  ├─ router.py
│  │  └─ workflow.py
│  ├─ providers/
│  │  ├─ base.py
│  │  ├─ azure_openai.py
│  │  ├─ anthropic.py
│  │  ├─ gemini.py
│  │  ├─ groq.py
│  │  └─ mistral.py
│  ├─ research/
│  │  ├─ search.py
│  │  ├─ extract.py
│  │  └─ rank.py
│  ├─ services/
│  │  ├─ orchestrator.py
│  │  ├─ citations.py
│  │  └─ evaluation.py
│  └─ utils/
│     ├─ logging.py
│     ├─ retry.py
│     └─ ids.py
├─ tests/
├─ .env.example
├─ docker-compose.yml
├─ Dockerfile
├─ pyproject.toml
└─ README.md
```

---

## Prompt Contracts

### Researcher system prompt
- Perform broad retrieval first, then narrow.
- Produce only supported factual statements.
- Label uncertain items as unresolved.
- Return a briefing with a source manifest.

### Synthesizer system prompt
- Write a complete answer using only the research brief.
- Distinguish evidence, interpretation, and assumptions.
- Cite inline where the API contract requires it.

### Adversary system prompt
- Critique aggressively but precisely.
- Find unsupported claims, reasoning gaps, omitted counterevidence, temporal ambiguity.
- Return structured critique items with severity and correction guidance.

### Moderator system prompt
- Decide whether the remaining issues materially affect correctness, nuance, or reliability.
- Return `revise` or `finalize`.
- Prevent unnecessary loops.

---

## Reliability Controls

### Timeouts
Set per-call limits and a total run budget.
- Search: 10–20 seconds
- Individual model call: 20–45 seconds
- Total workflow budget: 90–180 seconds depending on depth

### Retry policy
- exponential backoff
- retry only transient failures
- no blind retries for context-length or auth failures

### Fallbacks
- If Claude fails, synthesize with Gemini or Azure
- If search provider fails, switch to a secondary search API
- If moderator fails, use deterministic stop condition after max rounds

### Token budget management
- compress the research brief before synthesis
- pass deltas into later critique rounds instead of the full transcript
- keep a normalized claim list for compact verification

---

## Security Model

### Inbound auth
- API key or signed bearer token for GPT Action requests
- rate limit by client
- audit logs per request id

### Secrets handling
- never expose upstream provider keys to the GPT
- environment variables locally; vault/KMS in production

### Output hardening
- sanitize raw web content before model ingestion
- strip prompt injection patterns from retrieved pages
- mark external content as untrusted context

---

## Evaluation Strategy

You need a measurable way to verify the debate loop is actually improving answers.

### Build a benchmark set
Use 50–200 prompts across:
- technical research
- policy/legal summaries
- current-events synthesis
- scientific comparison
- adversarial misinformation checks

### Score dimensions
- factual accuracy
- citation quality
- completeness
- reasoning quality
- uncertainty calibration
- latency
- cost per run

### Compare modes
- single-model baseline
- search + single synthesis
- full round-table debate
- debate with 1 round vs 2–3 rounds

---

## Deployment Options

### Local development
- FastAPI + Docker Compose
- Expose via Cloudflare Tunnel or ngrok for GPT Action testing

### Production
- VPS, Fly.io, Render, Railway, Azure Container Apps, ECS, or Kubernetes
- prefer managed Postgres and Redis
- attach observability from day one

---

## Practical Recommendation

### Best first version
Do not start with every provider and every feature simultaneously. Start with:
- Search: Tavily
- Synthesizer: Claude
- Adversary: Azure OpenAI or Groq Llama
- Moderator: Gemini
- Optional researcher compression: Mistral

That gives you clear role separation without excessive orchestration complexity.

### First milestone
1. One endpoint: `/v1/debate`
2. One search provider
3. Four role nodes
4. Max 2 revision loops
5. Structured JSON response
6. GPT Action attached to the OpenAPI schema

---

## Implementation Sequence

1. Define request/response schemas
2. Build provider adapters
3. Add search integration
4. Implement LangGraph state and nodes
5. Add revision routing and stop conditions
6. Add structured logging and run ids
7. Expose `/v1/debate`
8. Validate with direct API tests
9. Import OpenAPI into GPT Actions / Create App
10. Tune prompts and stop criteria using benchmark prompts

---

## What to build next

### Phase 2
- source credibility scoring
- contradiction detection across sources
- claim-level citation checking
- streaming partial status updates
- human review mode
- cached result reuse for repeated questions

### Phase 3
- user-selectable debate depth
- domain-specific panels, e.g. legal panel, security panel, scientific panel
- cost-aware routing based on query complexity
- automatic model substitution on provider degradation

---

## Merlin's Knights of the Round Table: LangGraph Workflow

### Thematic role map
- **Merlin** = orchestrator
- **Sir Bedivere** = Researcher
- **Sir Percival** = Evidence Builder
- **Sir Lancelot** = Conceptualizer / Planner
- **Round Table Council** = Debate Panel
- **The Crown** = Judge
- **Sir Kay** = Builder
- **Sir Bors** = Debugger
- **The Chronicle** = Finalizer

---

## Operational graph

### Flow
```text
START
  -> bedivere_research
  -> percival_evidence
  -> lancelot_plan
  -> round_table_debate
  -> crown_judge
      -> if revision_required: lancelot_replan -> round_table_debate -> crown_judge
      -> if approved: kay_build
  -> bors_debug
      -> if hard_failure: bedivere_targeted_debug_research -> bors_debug
      -> if success: chronicle_finalize
  -> END
```

### Decision logic

#### Crown Judge routing
- `APPROVED` -> builder
- `REVISION_REQUIRED` -> planner
- `EVIDENCE_INSUFFICIENT` -> researcher
- `CONTRADICTION_FOUND` -> evidence builder or planner depending on severity

#### Bors Debug routing
- `SUCCESS` -> finalizer
- `PATCH_REQUIRED` -> debugger retry loop
- `DOC_RESEARCH_REQUIRED` -> targeted debug research
- `BLOCKED` -> finalizer with known issues and blocker report

---

## State model for Merlin

```python
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
    query: str
    objective: str = ""
    research_notes: str = ""
    evidence_report: str = ""
    implementation_plan: str = ""
    draft_answer: str = ""
    draft_code_summary: str = ""
    debug_notes: str = ""
    final_answer: str = ""

    sources: list[SourceItem] = Field(default_factory=list)
    claims: list[ClaimItem] = Field(default_factory=list)
    critiques: list[CritiqueItem] = Field(default_factory=list)
    artifacts: list[ArtifactItem] = Field(default_factory=list)

    judge_decision: JudgeDecision | None = None
    debug_decision: DebugDecision | None = None

    debate_round: int = 0
    max_debate_rounds: int = 3
    debug_round: int = 0
    max_debug_rounds: int = 3

    run_status: Literal["running", "complete", "blocked", "failed"] = "running"
    confidence: float | None = None
    model_trace: list[dict[str, Any]] = Field(default_factory=list)
```

---

## Node contracts

### 1. `bedivere_research`
**Input:** user query, optional domain constraints  
**Output:** research notes, source manifest, unresolved questions

Responsibilities:
- expand the query into research tasks
- collect relevant sources
- prioritize official docs, primary sources, issue trackers, standards, and recent references
- filter prompt-injection-like content from retrieved pages

Expected state updates:
- `research_notes`
- `sources`
- `model_trace`

### 2. `percival_evidence`
**Input:** research notes + sources  
**Output:** structured evidence report + claim inventory

Responsibilities:
- convert raw notes into usable evidence
- separate verified facts from open questions
- create an evidence report compact enough for downstream reasoning
- extract initial claims and attach evidence references

Expected state updates:
- `evidence_report`
- `claims`

### 3. `lancelot_plan`
**Input:** evidence report + claims  
**Output:** implementation plan or structured answer plan

Responsibilities:
- define architecture or answer structure
- identify assumptions, dependencies, risks, and milestones
- produce a concrete plan before debate begins

Expected state updates:
- `implementation_plan`
- `draft_answer`

### 4. `round_table_debate`
**Input:** implementation plan + evidence report + claims  
**Output:** critiques + revised plan

Debate protocol:
1. proposer presents plan
2. critic attacks unsupported assumptions, weak architecture, missing counterarguments, security issues, maintainability risks
3. reviser updates the plan
4. moderator summarizes unresolved issues

Expected state updates:
- `critiques`
- `implementation_plan`
- `debate_round += 1`

### 5. `crown_judge`
**Input:** revised plan + critiques + claims  
**Output:** routing decision

Responsibilities:
- verify that key claims are supported
- check that critiques were actually addressed
- reject plans with contradictions or insufficient evidence
- approve only when confidence threshold is met

Expected state updates:
- `judge_decision`
- updated `claims`
- optional `confidence`

### 6. `kay_build`
**Input:** approved plan  
**Output:** code/config/tests/docs artifacts

Responsibilities:
- implement the approved design
- generate code in bounded units
- create tests and configuration
- avoid introducing unapproved architectural drift

Expected state updates:
- `artifacts`
- `draft_code_summary`

### 7. `bors_debug`
**Input:** artifacts + test/lint/runtime feedback  
**Output:** patches or blockers

Responsibilities:
- run tests and inspect failures
- patch implementation issues
- classify hard failures that require targeted research

Expected state updates:
- `debug_notes`
- `debug_decision`
- `debug_round += 1`
- `artifacts` updated with patches

### 8. `bedivere_targeted_debug_research`
**Input:** specific error signatures or stack traces  
**Output:** targeted fix references

Responsibilities:
- search official docs, issue trackers, release notes, and known bug reports
- return only findings relevant to the exact failure mode

Expected state updates:
- `research_notes` append targeted findings
- `sources` append debug references

### 9. `chronicle_finalize`
**Input:** final artifacts + evidence + debug notes  
**Output:** final deliverable

Responsibilities:
- assemble final answer or package
- include summary of reasoning, evidence, key critiques, fixes, and known limitations
- provide confidence score and residual risk notes

Expected state updates:
- `final_answer`
- `run_status = complete` or `blocked`

---

## LangGraph skeleton

```python
from langgraph.graph import StateGraph, END
from app.graph.state import MerlinState
from app.graph.nodes import (
    bedivere_research,
    percival_evidence,
    lancelot_plan,
    round_table_debate,
    crown_judge,
    kay_build,
    bors_debug,
    bedivere_targeted_debug_research,
    chronicle_finalize,
)


def route_after_judge(state: MerlinState) -> str:
    if state.judge_decision == "APPROVED":
        return "kay_build"
    if state.judge_decision == "EVIDENCE_INSUFFICIENT":
        return "bedivere_research"
    if state.debate_round >= state.max_debate_rounds:
        return "chronicle_finalize"
    return "lancelot_plan"


def route_after_debug(state: MerlinState) -> str:
    if state.debug_decision == "SUCCESS":
        return "chronicle_finalize"
    if state.debug_decision == "DOC_RESEARCH_REQUIRED" and state.debug_round < state.max_debug_rounds:
        return "bedivere_targeted_debug_research"
    if state.debug_decision == "PATCH_REQUIRED" and state.debug_round < state.max_debug_rounds:
        return "bors_debug"
    return "chronicle_finalize"


def build_graph():
    graph = StateGraph(MerlinState)

    graph.add_node("bedivere_research", bedivere_research)
    graph.add_node("percival_evidence", percival_evidence)
    graph.add_node("lancelot_plan", lancelot_plan)
    graph.add_node("round_table_debate", round_table_debate)
    graph.add_node("crown_judge", crown_judge)
    graph.add_node("kay_build", kay_build)
    graph.add_node("bors_debug", bors_debug)
    graph.add_node("bedivere_targeted_debug_research", bedivere_targeted_debug_research)
    graph.add_node("chronicle_finalize", chronicle_finalize)

    graph.set_entry_point("bedivere_research")
    graph.add_edge("bedivere_research", "percival_evidence")
    graph.add_edge("percival_evidence", "lancelot_plan")
    graph.add_edge("lancelot_plan", "round_table_debate")
    graph.add_edge("round_table_debate", "crown_judge")
    graph.add_conditional_edges("crown_judge", route_after_judge)
    graph.add_edge("kay_build", "bors_debug")
    graph.add_conditional_edges("bors_debug", route_after_debug)
    graph.add_edge("bedivere_targeted_debug_research", "bors_debug")
    graph.add_edge("chronicle_finalize", END)

    return graph.compile()
```

---

## FastAPI contract for Merlin

### `POST /v1/quests`
This is the main entry point for GPT / Create App.

Request example:
```json
{
  "query": "Build an MCP-backed research lab that coordinates Azure OpenAI, Claude, Gemini, Groq, and Mistral.",
  "mode": "build",
  "max_debate_rounds": 2,
  "max_debug_rounds": 2,
  "include_sources": true,
  "providers": {
    "researcher": "mistral-large-latest",
    "evidence": "claude-sonnet",
    "planner": "claude-sonnet",
    "critic": "azure:gpt-4.1",
    "judge": "gemini-2.0-flash",
    "builder": "claude-sonnet",
    "debugger": "azure:gpt-4.1"
  }
}
```

Response example:
```json
{
  "run_id": "quest_123",
  "status": "complete",
  "theme": "Merlin's Knights of the Round Table",
  "final_answer": "...",
  "confidence": 0.87,
  "judge_decision": "APPROVED",
  "artifacts": [
    {"path": "app/main.py", "artifact_type": "code"},
    {"path": "README.md", "artifact_type": "doc"}
  ],
  "sources": [
    {"title": "FastAPI docs", "url": "https://..."}
  ],
  "debate_summary": {
    "rounds": 2,
    "key_critiques": [
      "Original plan lacked a verification stage.",
      "Provider adapter abstraction was clarified."
    ]
  },
  "debug_summary": {
    "rounds": 1,
    "known_issues": []
  }
}
```

---

## Recommended provider-role mapping

### Fast path
- Bedivere / Researcher: Mistral or Gemini Flash
- Percival / Evidence Builder: Claude
- Lancelot / Planner: Claude
- Round Table Critic: Azure OpenAI or Groq Llama
- The Crown / Judge: Gemini
- Sir Kay / Builder: Claude or Azure OpenAI
- Sir Bors / Debugger: Claude or Azure OpenAI

### Why this split works
- Claude is strong at structured synthesis and implementation planning
- Gemini is strong as an evaluator/judge when prompts are tightly scoped
- Azure OpenAI or Groq-hosted Llama works well as an adversarial critic
- Mistral is cost-efficient for research compression and retrieval-oriented tasks

---

## Practical stop conditions

### Debate stop conditions
Stop debate when any of the following is true:
- judge returns `APPROVED`
- `debate_round >= max_debate_rounds`
- no high-severity critique remains
- evidence quality is too weak to justify stronger conclusions

### Debug stop conditions
Stop debugging when any of the following is true:
- tests pass or implementation is stable enough
- `debug_round >= max_debug_rounds`
- blocker depends on unavailable external information or environment

---

## Naming inside the codebase

Use functional names in code and reserve the Arthurian names for UI or docs.

Example:
- `research_node` instead of `bedivere_research`
- `judge_node` instead of `crown_judge`
- `debug_research_node` instead of `bedivere_targeted_debug_research`

Then map them in presentation:
```python
ROLE_LABELS = {
    "research_node": "Sir Bedivere",
    "evidence_node": "Sir Percival",
    "planner_node": "Sir Lancelot",
    "judge_node": "The Crown",
    "builder_node": "Sir Kay",
    "debugger_node": "Sir Bors",
}
```

This keeps the implementation maintainable while preserving the theme.

---

## Bottom line
The Merlin system should be implemented as a **LangGraph-controlled research-and-build quest engine** with bounded debate loops, a hard verification gate through the Judge, and a targeted debug-research loop for difficult failures. That gives you a coherent architecture, a strong product identity, and a practical path to a production-grade MCP-backed multi-model lab.

