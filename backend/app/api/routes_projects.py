"""
CodeBridge V1 - Projects API Routes
Endpoints for ingesting, querying, and managing codebases from local folders or GitHub.
"""
from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
import aiosqlite

from backend.app.config import DB_PATH
from backend.app.db.models import Project, BusinessDomainGroup, FileRecord
from backend.app.services.ingestion_service import IngestionService
from backend.app.services.summarizer_service import SummarizerService

router = APIRouter(prefix="/api/projects", tags=["Projects"])


class LocalIngestRequest(BaseModel):
    directory_path: str
    project_name: str = ""


class GitHubIngestRequest(BaseModel):
    repo_url: str
    github_token: str = ""


class ProjectDetailResponse(BaseModel):
    project: Project
    domains: List[BusinessDomainGroup]
    total_files: int
    total_symbols: int


@router.get("", response_model=List[Project])
async def list_projects():
    """Returns all ingested projects without redundant duplicates."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM projects ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        
        seen_keys = set()
        projects = []
        for r in rows:
            key = (r["source_type"], r["name"])
            if key in seen_keys:
                continue
            seen_keys.add(key)
            projects.append(
                Project(
                    id=r["id"],
                    name=r["name"],
                    source_type=r["source_type"],
                    source_path=r["source_path"],
                    executive_summary=r["executive_summary"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
            )
        return projects


@router.post("/local", response_model=dict)
async def ingest_local(req: LocalIngestRequest):
    """Ingests a project from a local directory."""
    try:
        project_id = await IngestionService.ingest_local_directory(
            directory_path=req.directory_path,
            project_name=req.project_name or None,
        )
        # Trigger background project summary generation
        summarizer = SummarizerService()
        await summarizer.generate_project_executive_summary(project_id)
        return {"success": True, "project_id": project_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/github", response_model=dict)
async def ingest_github(req: GitHubIngestRequest):
    """Ingests a project from a GitHub repository archive via REST API."""
    try:
        project_id = await IngestionService.ingest_github_repo(
            repo_url=req.repo_url,
            github_token=req.github_token or None,
        )
        summarizer = SummarizerService()
        await summarizer.generate_project_executive_summary(project_id)
        return {"success": True, "project_id": project_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(project_id: str):
    """Returns detailed project metadata, executive briefing, and domain hierarchy."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        proj_row = await cursor.fetchone()
        if not proj_row:
            raise HTTPException(status_code=404, detail="Project not found")

        project = Project(
            id=proj_row["id"],
            name=proj_row["name"],
            source_type=proj_row["source_type"],
            source_path=proj_row["source_path"],
            executive_summary=proj_row["executive_summary"],
            created_at=proj_row["created_at"],
            updated_at=proj_row["updated_at"],
        )

        # Query all files
        cursor = await db.execute(
            """
            SELECT id, project_id, relative_path, file_type, language, size_bytes, plain_summary, business_domain
            FROM files
            WHERE project_id = ?
            ORDER BY relative_path ASC
            """,
            (project_id,),
        )
        files_rows = await cursor.fetchall()

        cursor = await db.execute(
            """
            SELECT COUNT(*) as count FROM symbols s
            JOIN files f ON s.file_id = f.id
            WHERE f.project_id = ?
            """,
            (project_id,),
        )
        sym_count_row = await cursor.fetchone()
        total_symbols = sym_count_row["count"] if sym_count_row else 0

    # Group by domain
    domain_map = {}
    for r in files_rows:
        domain = r["business_domain"] or "General Application Logic"
        if domain not in domain_map:
            domain_map[domain] = []
        domain_map[domain].append(
            FileRecord(
                id=r["id"],
                project_id=r["project_id"],
                relative_path=r["relative_path"],
                file_type=r["file_type"],
                language=r["language"],
                size_bytes=r["size_bytes"],
                plain_summary=r["plain_summary"],
                business_domain=r["business_domain"],
            )
        )

    domains = [
        BusinessDomainGroup(domain_name=k, files=v)
        for k, v in sorted(domain_map.items(), key=lambda item: len(item[1]), reverse=True)
    ]

    return ProjectDetailResponse(
        project=project,
        domains=domains,
        total_files=len(files_rows),
        total_symbols=total_symbols,
    )


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Deletes a project and all associated files and symbols."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute(
            "DELETE FROM symbols WHERE file_id IN (SELECT id FROM files WHERE project_id = ?)",
            (project_id,),
        )
        await db.execute("DELETE FROM files WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        await db.commit()
    return {"success": True}


@router.get("/{project_id}/export")
async def export_project(project_id: str, format: str = "markdown"):
    """Exports an executive architecture briefing in Markdown or print-ready HTML."""
    from fastapi.responses import HTMLResponse, PlainTextResponse
    from backend.app.services.export_service import ExportService

    try:
        if format.lower() == "html":
            html = await ExportService.generate_html_report(project_id)
            return HTMLResponse(content=html)
        else:
            md = await ExportService.generate_markdown_report(project_id)
            return PlainTextResponse(content=md, media_type="text/markdown")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
