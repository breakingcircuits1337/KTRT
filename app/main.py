from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_health import router as health_router
from app.api.routes_quest import router as quest_router
from app.api.routes_search import router as search_router
from app.utils.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    # Pre-compile the LangGraph workflow so first request is fast
    from app.graph.workflow import get_graph
    get_graph()
    yield


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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(quest_router)
app.include_router(search_router)
