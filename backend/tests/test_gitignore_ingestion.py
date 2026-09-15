"""
Unit tests for .gitignore pathspec filtering during repository ingestion
"""
import pytest
import tempfile
import aiosqlite
from pathlib import Path

from backend.app.config import DB_PATH
from backend.app.db.database import init_db
from backend.app.services.ingestion_service import IngestionService


@pytest.mark.asyncio
async def test_gitignore_filtering():
    await init_db()

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / ".gitignore").write_text("*.secret\nignored_folder/\n")
        (root / "app.py").write_text("def hello(): return 'world'")
        (root / "credentials.secret").write_text("API_KEY=12345")
        (root / "ignored_folder").mkdir()
        (root / "ignored_folder" / "internal.py").write_text("def internal(): pass")

        proj_id = await IngestionService.ingest_local_directory(str(root), project_name="GitIgnore Test")

        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT relative_path FROM files WHERE project_id = ?", (proj_id,))
            files = [r["relative_path"] for r in await cursor.fetchall()]

        assert "app.py" in files
        assert "credentials.secret" not in files
        assert not any("ignored_folder" in f for f in files)
