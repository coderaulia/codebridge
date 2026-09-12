"""
CodeBridge V1 - Files & Code API Routes
Provides endpoints for retrieving file source code, AST symbols, and line ranges.
"""
from pathlib import Path
from fastapi import APIRouter, HTTPException
import aiosqlite

from backend.app.config import DB_PATH
from backend.app.db.models import FileDetail, SymbolRecord

router = APIRouter(prefix="/api/files", tags=["Files"])


@router.get("/{file_id}", response_model=FileDetail)
async def get_file(file_id: str):
    """Retrieves full file content and extracted deterministic symbols for Monaco rendering."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """
            SELECT f.*, p.source_path
            FROM files f
            JOIN projects p ON f.project_id = p.id
            WHERE f.id = ?
            """,
            (file_id,),
        )
        file_row = await cursor.fetchone()
        if not file_row:
            raise HTTPException(status_code=404, detail="File not found")

        # Fetch extracted symbols
        cursor = await db.execute(
            """
            SELECT * FROM symbols
            WHERE file_id = ?
            ORDER BY start_line ASC
            """,
            (file_id,),
        )
        symbols_rows = await cursor.fetchall()

    # Read content from disk
    source_root = Path(file_row["source_path"])
    full_path = source_root / file_row["relative_path"]

    content = ""
    if full_path.exists():
        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            content = f"// Error reading file content from {full_path}"
    else:
        content = f"// File not found on disk: {full_path}"

    symbols = [
        SymbolRecord(
            id=s["id"],
            file_id=s["file_id"],
            name=s["name"],
            symbol_type=s["symbol_type"],
            start_line=s["start_line"],
            end_line=s["end_line"],
            signature=s["signature"],
            parameters_json=s["parameters_json"],
        )
        for s in symbols_rows
    ]

    return FileDetail(
        id=file_row["id"],
        project_id=file_row["project_id"],
        relative_path=file_row["relative_path"],
        file_type=file_row["file_type"],
        language=file_row["language"],
        size_bytes=file_row["size_bytes"],
        plain_summary=file_row["plain_summary"],
        business_domain=file_row["business_domain"],
        content=content,
        symbols=symbols,
    )
