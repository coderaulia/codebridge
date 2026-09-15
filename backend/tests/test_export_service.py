"""
Unit tests for Executive Architecture Export Engine
"""
import pytest
from pathlib import Path
from backend.app.db.database import init_db
from backend.app.services.ingestion_service import IngestionService
from backend.app.services.export_service import ExportService


@pytest.mark.asyncio
async def test_export_reports():
    await init_db()
    app_path = Path("examples/ecommerce-app").resolve()

    proj_id = await IngestionService.ingest_local_directory(str(app_path), project_name="Export Test App")

    # Test Markdown report
    md_report = await ExportService.generate_markdown_report(proj_id)
    assert "CodeBridge Executive Architecture Briefing" in md_report
    assert "Business Domain Architecture" in md_report
    assert "Data Persistence & Relational Schema" in md_report

    # Test HTML report
    html_report = await ExportService.generate_html_report(proj_id)
    assert "<!DOCTYPE html>" in html_report
    assert "Print / Save as PDF" in html_report
