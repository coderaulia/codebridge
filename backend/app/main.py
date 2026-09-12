"""
CodeBridge V1 - FastAPI Application Entrypoint
Orchestrates API routes, CORS policies, SQLite database lifecycle, and SSE streams.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.db.database import init_db
from backend.app.api.routes_projects import router as projects_router
from backend.app.api.routes_files import router as files_router
from backend.app.api.routes_translate import router as translate_router
from backend.app.api.routes_settings import router as settings_router
from backend.app.api.routes_system import router as system_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes SQLite database tables and seeds default provider on startup."""
    await init_db()
    yield


app = FastAPI(
    title="CodeBridge - Local Codebase Analyzer by Vanaila",
    description="Deterministic AST parsing and AI-powered non-technical translation engine.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(projects_router)
app.include_router(files_router)
app.include_router(translate_router)
app.include_router(settings_router)
app.include_router(system_router)


@app.get("/api/health")
async def health_check():
    """Simple ping to verify server health."""
    return {"status": "ok", "service": "CodeBridge V1 API"}
