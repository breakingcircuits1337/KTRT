<div align="center">

<img src="KTRT/ChatGPT Image Mar 13, 2026, 06_39_46 PM.png" width="220" alt="KTRT Logo" />

# KTRT
### Knights of the Round Table Research

**A multi-model adversarial AI research lab — where the greatest minds of every era debate, build, and deliver.**

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Workflow_Engine-FF6B35?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/License-MIT-gold?style=for-the-badge)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-22_Passing-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](tests/)

<br/>

> *"Speak your request, and we shall illuminate the path —*
> *whether it be an answer to your question, or the blueprint for an application."*
> — Merlin

<br/>

<img src="KTRT/ChatGPT Image Mar 13, 2026, 08_28_52 PM.png" width="420" alt="KTRT Round Table" />

</div>

---

## What is KTRT?

KTRT is a **production-grade multi-model orchestration service** that assembles five AI providers — Claude, Azure OpenAI, Gemini, Groq, and Mistral — into a structured adversarial research workflow inspired by the legend of King Arthur's Round Table.

Instead of sending your question to a single model and hoping for the best, KTRT deploys a **council of specialized AI knights**, each with a defined role, who research, debate, build, debug, and finalize before delivering a consensus answer with citations, confidence scores, and full reasoning traces.

**This is not a chatbot. It is a research-and-build lab.**

<br/>

<div align="center">
<img src="KTRT/ChatGPT Image Mar 13, 2026, 06_44_03 PM.png" width="420" alt="KTRT Quest UI" />
</div>

---

## The Knights

Each AI role is assigned to the model best suited for it. Roles are overridable per-request.

| Knight | Role | Default Model | Responsibility |
|--------|------|--------------|----------------|
| **Sir Bedivere** | Researcher | Mistral Large | Web research, source retrieval, factual grounding |
| **Sir Percival** | Evidence Builder | Claude Sonnet | Synthesize raw notes into structured evidence reports |
| **Sir Lancelot** | Planner | Claude Sonnet | Define architecture, identify risks, draft the plan |
| **Round Table** | Debate Panel | Groq / Llama | Adversarial critique — attack weak claims and assumptions |
| **The Crown** | Judge | Gemini Flash | Verify claims, gate the plan, route the decision |
| **Sir Kay** | Builder | Claude Sonnet | Implement the approved plan into artifacts |
| **Sir Bors** | Debugger | Azure OpenAI | Diagnose failures, patch, research fixes |
| **The Chronicle** | Finalizer | Claude Sonnet | Assemble the final deliverable with sources and confidence |

---

## The Quest Engine

Every query becomes a **quest** — a stateful, multi-stage workflow that runs through a LangGraph state machine with bounded debate and debug loops.

```
User Query
    │
    ▼
Sir Bedivere ──── Web Research ──── Source Manifest
    │
    ▼
Sir Percival ──── Evidence Report ──── Claims Inventory
    │
    ▼
Sir Lancelot ──── Implementation Plan
    │
    ▼
Round Table ──── Adversarial Critique ─────────────────────┐
    │                                                        │
    ▼                                                        │
The Crown ─── APPROVED ──────────────── Sir Kay (Build)     │
              REVISION_REQUIRED ────────────────────────────┘
              EVIDENCE_INSUFFICIENT ── Sir Bedivere (re-research)
    │
    ▼
Sir Bors ──── Debug & Patch ────── DOC_RESEARCH ── Sir Bedivere (targeted)
    │
    ▼
The Chronicle ──── Final Answer + Citations + Confidence Score
```

**Debate stops when:** the Judge approves, max rounds are reached, or no high-severity critiques remain.
**Debug stops when:** all tests pass, max rounds are reached, or the failure is classified as blocked.

---

## Results & Debug Diagnostics

<div align="center">
<img src="KTRT/ChatGPT Image Mar 13, 2026, 07_51_57 PM.png" width="700" alt="KTRT Results and Debug View" />
</div>

---

## API

### `POST /v1/quests`

The single entry point for GPT Actions, Create App integrations, or direct API calls.

**Request:**
```json
{
  "query": "Design a fault-tolerant event-driven payment processing system",
  "mode": "build",
  "max_debate_rounds": 3,
  "max_debug_rounds": 2,
  "include_sources": true,
  "providers": {
    "researcher": "mistral-large-latest",
    "critic":     "groq:llama-3.3-70b",
    "judge":      "gemini-2.0-flash",
    "builder":    "claude-sonnet-4-6"
  }
}
```

**Response:**
```json
{
  "run_id": "quest_4a7f3c9e1b2d",
  "status": "complete",
  "theme": "Merlin's Knights of the Round Table",
  "final_answer": "...",
  "confidence": 0.89,
  "debate_summary": {
    "rounds": 2,
    "judge_decision": "APPROVED",
    "key_critiques": [
      "[HIGH] Idempotency key strategy was undefined — added per-event deduplication.",
      "[MEDIUM] Dead-letter queue handling was missing — added DLQ with alerting."
    ]
  },
  "debug_summary": {
    "rounds": 1,
    "decision": "SUCCESS",
    "known_issues": []
  },
  "artifacts": [
    { "path": "app/payment_processor.py", "artifact_type": "code" },
    { "path": "tests/test_payment.py",    "artifact_type": "test" },
    { "path": "infra/kafka.yaml",         "artifact_type": "config" }
  ],
  "sources": [
    { "title": "Stripe Idempotency Docs", "url": "https://stripe.com/docs/..." }
  ]
}
```

### Additional Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/healthz` | Health check |
| `GET` | `/docs` | Interactive OpenAPI UI |
| `GET` | `/openapi.json` | OpenAPI schema (import into GPT Actions) |
| `POST` | `/v1/search` | Direct search endpoint |

---

## Project Structure

```
ktrt/
├── app/
│   ├── main.py                     # FastAPI app + lifespan
│   ├── config.py                   # Settings from environment
│   │
│   ├── graph/
│   │   ├── state.py                # MerlinState — full workflow state
│   │   ├── nodes.py                # All 9 knight implementations
│   │   ├── prompts.py              # System prompt contracts per role
│   │   ├── router.py               # Judge + Debug conditional routing
│   │   └── workflow.py             # LangGraph StateGraph compilation
│   │
│   ├── providers/
│   │   ├── base.py                 # LLMAdapter ABC + ModelTrace
│   │   ├── registry.py             # Role → adapter resolution
│   │   ├── anthropic.py            # Claude adapter
│   │   ├── azure_openai.py         # Azure OpenAI adapter
│   │   ├── gemini.py               # Gemini adapter
│   │   ├── groq.py                 # Groq adapter
│   │   └── mistral.py              # Mistral adapter
│   │
│   ├── research/
│   │   ├── search.py               # Tavily → Exa fallback search
│   │   ├── extract.py              # Page extraction + injection sanitization
│   │   └── rank.py                 # Credibility scoring + deduplication
│   │
│   ├── api/
│   │   ├── routes_quest.py         # POST /v1/quests
│   │   ├── routes_search.py        # POST /v1/search
│   │   └── routes_health.py        # GET /healthz
│   │
│   ├── services/
│   │   └── orchestrator.py         # Request → graph → response
│   │
│   └── utils/
│       ├── ids.py                   # Run ID / claim ID generation
│       ├── logging.py               # Structured logging (structlog)
│       └── retry.py                 # Exponential backoff decorator
│
├── tests/                           # 22 tests — schemas, routing, research
├── .env.example                     # All environment variables documented
├── docker-compose.yml               # API + Redis + Postgres
├── Dockerfile
└── pyproject.toml
```

---

## Getting Started

### 1. Configure environment

```bash
cp .env.example .env
```

Fill in the providers you want to use. At minimum you need **one search key** (Tavily or Exa) and keys for the models used in your target roles.

```env
KTRT_API_KEY=<your-inbound-api-key>

ANTHROPIC_API_KEY=<your-anthropic-key>
AZURE_OPENAI_API_KEY=<your-azure-key>
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
GOOGLE_API_KEY=<your-google-key>
GROQ_API_KEY=<your-groq-key>
MISTRAL_API_KEY=<your-mistral-key>

TAVILY_API_KEY=<your-tavily-key>
```

### 2. Run with Docker Compose

```bash
docker compose up
```

This starts the API on `http://localhost:8000` along with Redis and Postgres.

### 3. Run directly

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

### 4. Send your first quest

```bash
curl -X POST http://localhost:8000/v1/quests \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{
    "query": "What are the architectural trade-offs between event sourcing and traditional CRUD at scale?",
    "mode": "research",
    "max_debate_rounds": 2
  }'
```

### 5. Open the interactive docs

```
http://localhost:8000/docs
```

---

## GPT Actions / Create App Integration

KTRT exposes a fully spec-compliant OpenAPI schema at `/openapi.json`.

To connect to a GPT or Create App:
1. Import the schema from `http://your-host/openapi.json`
2. Set the action to `POST /v1/quests`
3. Add your `KTRT_API_KEY` as the bearer token
4. Set the GPT system prompt:

> *You are the front-end interface for a multi-model research lab called KTRT. For any substantive question or build request, call `create_quest`. Do not answer from internal knowledge when the tool is available. Present the returned consensus answer clearly, preserving source links, confidence notes, and caveats.*

---

## Reliability

| Concern | Approach |
|---------|----------|
| **Provider failures** | Per-adapter exponential backoff (3 attempts, 2–30s) |
| **Rate limits** | `TransientError` → retry; auth/context errors → fail fast |
| **Search provider failure** | Tavily → Exa automatic fallback |
| **Moderator failure** | Deterministic stop at `max_debate_rounds` |
| **Workflow timeout** | Configurable total budget (default 180s) |
| **Prompt injection** | Web content sanitized before model ingestion |
| **Token bloat** | Deltas passed between debate rounds, not full transcript |

---

## Provider Role Reference

| Role | Fast Path | Why |
|------|-----------|-----|
| Researcher | Mistral Large | Cost-efficient for retrieval and compression tasks |
| Evidence / Planner / Builder | Claude Sonnet | Strong at structured synthesis and implementation |
| Critic / Adversary | Groq Llama 3.3 70B | Fast, aggressive, cost-effective red-teaming |
| Judge | Gemini Flash | Strong evaluator when prompts are tightly scoped |
| Debugger | Azure OpenAI GPT-4.1 | Reliable for systematic failure analysis |

All role assignments are **overridable per-request** via the `providers` field.

---

## Development

```bash
# Install with dev extras
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint
ruff check app/ tests/

# Type check
mypy app/
```

---

## Roadmap

**Phase 2**
- [ ] Streaming partial status updates (SSE)
- [ ] Source credibility scoring with contradiction detection
- [ ] Claim-level citation verification
- [ ] Human review mode (pause for approval before build)
- [ ] Result caching for repeated queries

**Phase 3**
- [ ] Domain-specific debate panels (legal, security, scientific)
- [ ] Cost-aware model routing based on query complexity
- [ ] Automatic provider substitution on degradation
- [ ] Persistent run history and replay

---

<div align="center">

<img src="KTRT/ChatGPT Image Mar 13, 2026, 08_30_54 PM.png" width="420" alt="KTRT Round Table Scene" />

<br/><br/>

*The Round Table convenes. The quest begins.*

<br/>

**Built with Claude · Powered by LangGraph · Forged in Python**

</div>
