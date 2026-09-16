"""
CodeBridge V1 - Projects API Routes
Endpoints for ingesting, querying, and managing codebases from local folders or GitHub.
"""
import asyncio
from typing import List, Optional, Dict
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
import aiosqlite

from backend.app.config import DB_PATH
from backend.app.db.models import Project, BusinessDomainGroup, FileRecord
from backend.app.services.ingestion_service import IngestionService
from backend.app.services.summarizer_service import SummarizerService

router = APIRouter(prefix="/api/projects", tags=["Projects"])


class ScanStatus(BaseModel):
    total: int
    completed: int
    current_file: Optional[str] = None
    is_scanning: bool
    error: Optional[str] = None


_scan_tasks: Dict[str, ScanStatus] = {}


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
    macro_diagram: Optional[str] = None


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

        summary = r["plain_summary"] or ""
        is_placeholder = not summary or (summary.startswith("Provides ") and "logic for the application" in summary)
        has_expl = not is_placeholder and len(summary) > 10
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
                has_explanation=has_expl,
            )
        )

    summarizer = SummarizerService()
    macro_diagram = await summarizer.generate_project_macro_diagram(project_id)

    domains = [
        BusinessDomainGroup(
            domain_name=k,
            description=f"Coordinates {k.lower()} operations across {len(v)} components.",
            files=v,
        )
        for k, v in sorted(domain_map.items(), key=lambda item: len(item[1]), reverse=True)
    ]

    return ProjectDetailResponse(
        project=project,
        domains=domains,
        total_files=len(files_rows),
        total_symbols=total_symbols,
        macro_diagram=macro_diagram,
    )


@router.post("/{project_id}/scan-translations", response_model=ScanStatus)
async def start_project_translation_scan(project_id: str):
    """Starts or monitors background AI translation & summarization scanner for the project."""
    current = _scan_tasks.get(project_id)
    if current and current.is_scanning:
        return current

    # Count how many files need scanning
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT COUNT(*) as count FROM files WHERE project_id = ?", (project_id,))
        total_row = await cursor.fetchone()
        total_count = total_row["count"] if total_row else 0

        cursor = await db.execute(
            """
            SELECT COUNT(*) as count FROM files
            WHERE project_id = ?
            AND (plain_summary IS NULL OR plain_summary = '' OR plain_summary LIKE 'Provides %logic for the application%')
            """,
            (project_id,),
        )
        unexplained_row = await cursor.fetchone()
        unexplained_count = unexplained_row["count"] if unexplained_row else 0

    if unexplained_count == 0:
        status = ScanStatus(
            total=total_count,
            completed=total_count,
            current_file=None,
            is_scanning=False,
        )
        _scan_tasks[project_id] = status
        return status

    completed_init = total_count - unexplained_count
    status = ScanStatus(
        total=total_count,
        completed=completed_init,
        current_file="Initializing AI scanner...",
        is_scanning=True,
    )
    _scan_tasks[project_id] = status

    async def _run_background_scan():
        try:
            summarizer = SummarizerService()

            def _on_progress(completed: int, total_unexplained: int, current_file: str):
                _scan_tasks[project_id] = ScanStatus(
                    total=total_count,
                    completed=min(total_count, completed_init + completed),
                    current_file=current_file,
                    is_scanning=True,
                )

            await summarizer.generate_all_file_summaries(
                project_id=project_id,
                progress_callback=_on_progress,
            )
            await summarizer.generate_project_executive_summary(project_id)

            _scan_tasks[project_id] = ScanStatus(
                total=total_count,
                completed=total_count,
                current_file="Completed",
                is_scanning=False,
            )
        except Exception as e:
            _scan_tasks[project_id] = ScanStatus(
                total=total_count,
                completed=_scan_tasks[project_id].completed if project_id in _scan_tasks else 0,
                current_file="",
                is_scanning=False,
                error=str(e),
            )

    asyncio.create_task(_run_background_scan())
    return status


@router.get("/{project_id}/scan-status", response_model=ScanStatus)
async def get_project_scan_status(project_id: str):
    """Retrieves current background scanning progress for a project."""
    if project_id in _scan_tasks and _scan_tasks[project_id].is_scanning:
        return _scan_tasks[project_id]

    # Calculate completed vs total from DB
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT COUNT(*) as count FROM files WHERE project_id = ?", (project_id,))
        total_row = await cursor.fetchone()
        total = total_row["count"] if total_row else 0

        cursor = await db.execute(
            """
            SELECT COUNT(*) as count FROM files
            WHERE project_id = ?
            AND plain_summary IS NOT NULL
            AND plain_summary != ''
            AND plain_summary NOT LIKE 'Provides %logic for the application%'
            """,
            (project_id,),
        )
        done_row = await cursor.fetchone()
        completed = done_row["count"] if done_row else 0

    return ScanStatus(
        total=total,
        completed=completed,
        current_file=None,
        is_scanning=False,
    )


@router.post("/{project_id}/generate-summaries", response_model=dict)
async def generate_project_summaries(project_id: str):
    """Generates bottom-up AI file and domain summaries across the project."""
    summarizer = SummarizerService()
    count = await summarizer.generate_all_file_summaries(project_id)
    await summarizer.generate_project_executive_summary(project_id)
    return {"success": True, "files_summarized": count}


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
