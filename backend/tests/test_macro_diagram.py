"""
Unit tests for Macro System Architecture Diagram and Level 1 & 2 Summarizer.
"""
import pytest
from backend.app.services.diagram_service import DiagramService
from backend.app.services.summarizer_service import SummarizerService
from backend.app.db.database import init_db
import aiosqlite
from backend.app.config import DB_PATH


def test_generate_macro_architecture_diagram_multi_tier():
    domains = [
        {"domain_name": "User Interface & Experience", "file_count": 12},
        {"domain_name": "API & External Communication", "file_count": 8},
        {"domain_name": "Identity & Access Control", "file_count": 4},
        {"domain_name": "Financial & Payment Processing", "file_count": 6},
        {"domain_name": "Data Persistence & Schemas", "file_count": 3},
        {"domain_name": "Analytics & Observability", "file_count": 2},
    ]

    diagram = DiagramService.generate_macro_architecture_diagram(domains)
    assert "flowchart TD" in diagram
    assert "UI_Layer" in diagram
    assert "API_Layer" in diagram
    assert "Service_Layer" in diagram
    assert "Data_Layer" in diagram
    assert "Infra_Layer" in diagram
    assert "User_Interface___Experience" in diagram
    assert "Financial___Payment_Processing" in diagram
    assert "classDef ui" in diagram


def test_generate_macro_architecture_diagram_empty():
    diagram = DiagramService.generate_macro_architecture_diagram([])
    assert diagram == ""


@pytest.mark.asyncio
async def test_summarizer_level1_and_level2():
    await init_db()

    # Seed test project and file in SQLite
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO projects (id, name, source_type, source_path) VALUES ('proj_test_c', 'TestProject', 'local', '/tmp')"
        )
        await db.execute(
            """
            INSERT OR REPLACE INTO files (id, project_id, relative_path, file_type, language, size_bytes, plain_summary, business_domain)
            VALUES ('file_test_c', 'proj_test_c', 'src/billing/stripe.ts', 'code', 'typescript', 1024, 'placeholder', 'Financial & Payment Processing')
            """
        )
        await db.execute(
            """
            INSERT OR REPLACE INTO symbols (id, file_id, name, symbol_type, start_line, end_line, signature)
            VALUES ('sym_test_c', 'file_test_c', 'createSubscription', 'function', 1, 25, 'export async function createSubscription(planId: string)')
            """
        )
        await db.commit()

    summarizer = SummarizerService()

    # Test Level 1 file summary
    file_summary = await summarizer.generate_file_summary('file_test_c')
    assert file_summary is not None
    assert len(file_summary) > 10

    # Test Level 2 domain summary
    domain_summary = await summarizer.generate_domain_summary('proj_test_c', 'Financial & Payment Processing')
    assert domain_summary is not None
    assert len(domain_summary) > 10

    # Test Macro diagram from project
    macro_diag = await summarizer.generate_project_macro_diagram('proj_test_c')
    assert "flowchart TD" in macro_diag
