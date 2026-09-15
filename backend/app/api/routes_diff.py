"""
CodeBridge V1 - Git Diff & Pull Request API Routes
Provides endpoints to translate raw diffs and extract live git changes into executive release notes.
"""
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
import aiosqlite

from backend.app.config import DB_PATH
from backend.app.services.diff_service import DiffService, DiffAnalysisResult

router = APIRouter(prefix="/api/diff", tags=["Diff & Releases"])


class DiffTranslateRequest(BaseModel):
    diff_text: str
    project_id: Optional[str] = None
    project_name: Optional[str] = ""


class LocalDiffResponse(BaseModel):
    has_git: bool
    diff_text: str
    message: str


@router.post("/translate", response_model=DiffAnalysisResult)
async def translate_diff(req: DiffTranslateRequest):
    """Translates a git diff or Pull Request into a 4-part executive release note."""
    if not req.diff_text.strip():
        raise HTTPException(status_code=400, detail="Diff text cannot be empty.")

    service = DiffService()
    return await service.translate_diff(
        diff_text=req.diff_text,
        project_name=req.project_name or "",
    )


@router.get("/local/{project_id}", response_model=LocalDiffResponse)
async def get_local_project_diff(project_id: str):
    """Fetches live uncommitted git diff from a local repository."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        proj = await cursor.fetchone()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")

    if proj["source_type"] != "local":
        return LocalDiffResponse(
            has_git=False,
            diff_text="",
            message="Project was ingested from a remote archive without local git history.",
        )

    diff_content = DiffService.get_local_git_diff(proj["source_path"])
    if not diff_content:
        return LocalDiffResponse(
            has_git=True,
            diff_text="",
            message="No uncommitted working tree or staged changes found in repository.",
        )

    return LocalDiffResponse(
        has_git=True,
        diff_text=diff_content,
        message=f"Found uncommitted changes in {proj['name']}.",
    )
