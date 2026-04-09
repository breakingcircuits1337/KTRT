from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_health import router as health_router
from app.api.routes_quest import router as quest_router
from app.api.routes_search import router as search_router
from app.config import settings
from app.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    if not settings.ktrt_api_key:
        logger.warning(
            "KTRT_API_KEY is not set — all API requests will be rejected with 503. "
            "Set KTRT_API_KEY in your environment before accepting traffic."
        )

    # Pre-compile the LangGraph workflow so first request is fast
    from app.graph.workflow import get_graph
    get_graph()
    yield


def _cors_origins() -> list[str]:
    raw = settings.cors_origins.strip()
    if raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


app = FastAPI(
    title="KTRT — Knights of the Round Table Research",
    description=(
        "Multi-model adversarial research orchestration service. "
        "Coordinates Azure OpenAI, Claude, Gemini, Groq, and Mistral into "
        "a structured research-and-build workflow modeled on Merlin's Knights."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    # Credentials (cookies) are not used — API key auth only.
    # allow_credentials must stay False when allow_origins contains "*".
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["X-API-Key", "Content-Type"],
)

app.include_router(health_router)
app.include_router(quest_router)
app.include_router(search_router)
