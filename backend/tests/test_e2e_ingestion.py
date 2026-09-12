"""
End-to-end integration test for CodeBridge V1 with sample e-commerce application
"""
import pytest
from pathlib import Path
import aiosqlite

from backend.app.config import DB_PATH
from backend.app.db.database import init_db
from backend.app.services.ingestion_service import IngestionService
from backend.app.services.summarizer_service import SummarizerService
from backend.app.services.translation_service import TranslationService
from backend.app.services.diagram_service import DiagramService
from backend.app.parsers.prisma_parser import PrismaParser


@pytest.mark.asyncio
async def test_e2e_sample_app_ingestion():
    await init_db()

    app_path = Path("examples/ecommerce-app").resolve()
    assert app_path.exists()

    proj_id = await IngestionService.ingest_local_directory(str(app_path), project_name="E-Commerce Demo")
    assert proj_id.startswith("proj_")

    # Verify files and symbols in SQLite
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute("SELECT * FROM files WHERE project_id = ?", (proj_id,))
        files = await cursor.fetchall()
        assert len(files) == 4

        domains = {f["business_domain"] for f in files}
        assert "Data Persistence & Schemas" in domains
        assert "Financial & Payment Processing" in domains
        assert "Identity & Access Control" in domains
        assert "Customer Communication & Alerts" in domains

        # Verify Prisma symbols
        prisma_file = next(f for f in files if f["language"] == "prisma")
        cursor = await db.execute("SELECT * FROM symbols WHERE file_id = ?", (prisma_file["id"],))
        prisma_symbols = await cursor.fetchall()
        model_names = [s["name"] for s in prisma_symbols]
        assert "User" in model_names
        assert "Order" in model_names
        assert "OrderItem" in model_names
        assert "Product" in model_names

    # Test Summarizer
    summarizer = SummarizerService()
    summary = await summarizer.generate_project_executive_summary(proj_id)
    assert summary != ""
    assert "E-Commerce Demo" in summary or "domain" in summary.lower()

    # Test ER diagram generation from Prisma
    prisma_content = Path("examples/ecommerce-app/prisma/schema.prisma").read_text()
    models = PrismaParser().parse_schema_models(prisma_content)
    er_diagram = DiagramService.generate_schema_er_diagram(models)
    assert "erDiagram" in er_diagram
    assert "User" in er_diagram
    assert "Order" in er_diagram

    # Test Translation Streaming generator
    trans_svc = TranslationService()
    events = []
    async for event in trans_svc.stream_translation(
        file_id=prisma_file["id"],
        start_line=1,
        end_line=25,
        selected_code=prisma_content[:200],
    ):
        events.append(event)

    assert len(events) > 0
    # Confirm cache write
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM translations_cache")
        cached = await cursor.fetchall()
        assert len(cached) >= 1
