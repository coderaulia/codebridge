"""
Unit tests for repository ingestion and symbol indexing
"""
import pytest
from pathlib import Path
import aiosqlite

from backend.app.config import DB_PATH
from backend.app.db.database import init_db
from backend.app.services.ingestion_service import IngestionService, classify_business_domain


def test_business_domain_classification():
    assert classify_business_domain("src/auth/jwt.ts") == "Identity & Access Control"
    assert classify_business_domain("src/billing/stripe.ts") == "Financial & Payment Processing"
    assert classify_business_domain("prisma/schema.prisma") == "Data Persistence & Schemas"
    assert classify_business_domain("src/api/routes.py") == "API & External Communication"
    assert classify_business_domain("src/components/Header.tsx") == "User Interface & Experience"


@pytest.mark.asyncio
async def test_local_ingest(tmp_path: Path):
    await init_db()

    # Create dummy project
    auth_file = tmp_path / "auth.py"
    auth_file.write_text("""
def login_user(username: str):
    return {"token": "xyz"}
""")

    schema_file = tmp_path / "schema.prisma"
    schema_file.write_text("""
model User {
  id    Int    @id @default(autoincrement())
  email String @unique
}
""")

    proj_id = await IngestionService.ingest_local_directory(str(tmp_path), project_name="TestApp")
    assert proj_id.startswith("proj_")

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM files WHERE project_id = ?", (proj_id,))
        files = await cursor.fetchall()
        assert len(files) == 2

        cursor = await db.execute(
            """
            SELECT s.* FROM symbols s
            JOIN files f ON s.file_id = f.id
            WHERE f.project_id = ?
            """,
            (proj_id,),
        )
        symbols = await cursor.fetchall()
        sym_names = [s["name"] for s in symbols]
        assert "login_user" in sym_names
        assert "User" in sym_names
