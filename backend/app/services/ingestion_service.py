"""
CodeBridge V1 - Repository Ingestion Engine
Handles local directory scanning and remote GitHub zipball streaming with deterministic symbol extraction.
"""
import os
import io
import uuid
import zipfile
from pathlib import Path
from typing import Tuple, List, Optional
import httpx
import aiosqlite

from backend.app.config import DB_PATH, REPOS_DIR
from backend.app.parsers import get_parser_for_file
from backend.app.parsers.prisma_parser import PrismaParser
from backend.app.parsers.sql_parser import SqlParser
from backend.app.parsers.drizzle_parser import DrizzleParser

EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    "__pycache__",
    ".next",
    ".nuxt",
    ".turbo",
    ".idea",
    ".vscode",
    "coverage",
}

EXCLUDED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".pdf", ".zip", ".tar", ".gz", ".7z",
    ".exe", ".dll", ".so", ".dylib", ".wasm",
    ".bin", ".pyc", ".lock", ".log",
}

DOMAIN_PATTERNS = [
    (["auth", "login", "jwt", "session", "user", "account"], "Identity & Access Control"),
    (["billing", "payment", "stripe", "checkout", "subscription", "pricing", "order"], "Financial & Payment Processing"),
    (["notification", "email", "sms", "alert", "push", "mailer"], "Customer Communication & Alerts"),
    (["schema", "model", "migration", "prisma", "database", "db", "repository"], "Data Persistence & Schemas"),
    (["api", "routes", "endpoint", "controller", "handler", "v1", "v2"], "API & External Communication"),
    (["ui", "component", "page", "view", "layout", "modal"], "User Interface & Experience"),
    (["analytics", "telemetry", "metric", "logging", "audit"], "Analytics & Observability"),
    (["service", "workflow", "worker", "job", "queue"], "Core Business Workflows"),
]


def classify_business_domain(rel_path: str) -> str:
    """Classifies a relative path into an intuitive business domain."""
    lowered = rel_path.lower()
    for keywords, domain in DOMAIN_PATTERNS:
        if any(k in lowered for k in keywords):
            return domain
    return "General Application Logic"


def classify_file_type(path: Path) -> Tuple[str, str]:
    """Returns (file_type, language)."""
    suffix = path.suffix.lower()
    name = path.name.lower()

    if suffix in (".ts", ".tsx"):
        return ("schema" if "schema" in name or "model" in name else "code", "typescript")
    if suffix in (".js", ".jsx", ".mjs"):
        return ("schema" if "schema" in name or "model" in name else "code", "javascript")
    if suffix in (".py", ".pyw"):
        return ("schema" if "models" in name or "schema" in name else "code", "python")
    if suffix == ".prisma":
        return ("schema", "prisma")
    if suffix == ".sql":
        return ("schema", "sql")
    if suffix in (".md", ".mdx", ".txt", ".rst"):
        return ("doc", "markdown")
    if suffix in (".json", ".yaml", ".yml", ".toml", ".env", ".ini"):
        return ("config", suffix.lstrip("."))

    return ("other", suffix.lstrip("."))


class IngestionService:
    """Orchestrates local directory and GitHub archive ingestion."""

    @staticmethod
    async def ingest_local_directory(directory_path: str, project_name: Optional[str] = None) -> str:
        """Ingests a directory from the local filesystem with intelligent path resolution."""
        raw_str = directory_path.strip()
        expanded = os.path.expanduser(raw_str)
        path = Path(expanded).resolve()

        if not path.exists() or not path.is_dir():
            # Try relative to home directory (e.g. user typed "Dev/myproject")
            home_candidate = (Path.home() / raw_str).resolve()
            if home_candidate.exists() and home_candidate.is_dir():
                path = home_candidate
            else:
                # Try relative to current working directory
                cwd_candidate = (Path.cwd() / raw_str).resolve()
                if cwd_candidate.exists() and cwd_candidate.is_dir():
                    path = cwd_candidate
                else:
                    raise ValueError(
                        f"Directory not found: '{directory_path}'. "
                        f"Checked '{path}' and '{home_candidate}'. "
                        "Please use the Folder Opener ('Browse...') button to select an existing folder."
                    )

        name = project_name or path.name

        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT id FROM projects WHERE source_path = ? OR (name = ? AND source_type = 'local')",
                (str(path), name),
            )
            existing = await cursor.fetchone()
            if existing:
                proj_id = existing[0]
                await db.execute(
                    "UPDATE projects SET name = ?, source_path = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (name, str(path), proj_id),
                )
                await db.execute(
                    "DELETE FROM symbols WHERE file_id IN (SELECT id FROM files WHERE project_id = ?)",
                    (proj_id,),
                )
                await db.execute("DELETE FROM files WHERE project_id = ?", (proj_id,))
                await db.commit()
            else:
                proj_id = f"proj_{uuid.uuid4().hex[:10]}"
                await db.execute(
                    """
                    INSERT INTO projects (id, name, source_type, source_path)
                    VALUES (?, ?, 'local', ?)
                    """,
                    (proj_id, name, str(path)),
                )
                await db.commit()

        await IngestionService._index_directory_files(proj_id, path)
        return proj_id

    @staticmethod
    async def ingest_github_repo(repo_url: str, github_token: Optional[str] = None) -> str:
        """Fetches and unzips a repository from GitHub API without local git binary."""
        clean_url = repo_url.strip().rstrip("/")
        # Extract owner/repo
        parts = clean_url.split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL format: '{repo_url}'. Expected 'https://github.com/owner/repo' or 'owner/repo'")

        owner = parts[-2]
        repo = parts[-1].replace(".git", "")

        proj_id = f"gh_{uuid.uuid4().hex[:10]}"
        target_dir = REPOS_DIR / proj_id
        target_dir.mkdir(parents=True, exist_ok=True)

        api_url = f"https://api.github.com/repos/{owner}/{repo}/zipball"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "CodeBridge-Ingestion-Agent",
        }
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            res = await client.get(api_url, headers=headers)
            if res.status_code != 200:
                raise RuntimeError(f"GitHub API returned HTTP {res.status_code}: {res.text[:200]}")

            zip_content = io.BytesIO(res.content)
            with zipfile.ZipFile(zip_content, "r") as z:
                # Path traversal safeguard
                for member in z.namelist():
                    resolved_path = (target_dir / member).resolve()
                    if not str(resolved_path).startswith(str(target_dir.resolve())):
                        raise SecurityError("Path traversal detected in zip archive.")
                z.extractall(target_dir)

        # Locate root directory inside extracted zip (GitHub zips typically have top-level dir owner-repo-hash)
        extracted_roots = [d for d in target_dir.iterdir() if d.is_dir()]
        root_dir = extracted_roots[0] if extracted_roots else target_dir
        repo_name = f"{owner}/{repo}"

        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT id FROM projects WHERE name = ? AND source_type = 'github'",
                (repo_name,),
            )
            existing = await cursor.fetchone()
            if existing:
                proj_id = existing[0]
                await db.execute(
                    "UPDATE projects SET source_path = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (str(root_dir), proj_id),
                )
                await db.execute(
                    "DELETE FROM symbols WHERE file_id IN (SELECT id FROM files WHERE project_id = ?)",
                    (proj_id,),
                )
                await db.execute("DELETE FROM files WHERE project_id = ?", (proj_id,))
                await db.commit()
            else:
                await db.execute(
                    """
                    INSERT INTO projects (id, name, source_type, source_path)
                    VALUES (?, ?, 'github', ?)
                    """,
                    (proj_id, repo_name, str(root_dir)),
                )
                await db.commit()

        await IngestionService._index_directory_files(proj_id, root_dir)
        return proj_id

    @staticmethod
    async def _index_directory_files(project_id: str, root_dir: Path) -> None:
        """Walks directory, extracts symbols deterministically, and stores in SQLite."""
        async with aiosqlite.connect(DB_PATH) as db:
            for dirpath, dirnames, filenames in os.walk(root_dir):
                # Filter out excluded directories
                dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS and not d.startswith(".")]

                for filename in filenames:
                    file_path = Path(dirpath) / filename
                    suffix = file_path.suffix.lower()

                    if suffix in EXCLUDED_EXTENSIONS or filename.startswith("."):
                        continue

                    try:
                        rel_path = str(file_path.relative_to(root_dir))
                    except ValueError:
                        rel_path = file_path.name

                    try:
                        stat = file_path.stat()
                        size = stat.st_size
                    except OSError:
                        continue

                    # Skip very large files (> 1MB) for code parsing
                    if size > 1_048_576:
                        continue

                    try:
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                    except Exception:
                        continue

                    file_type, language = classify_file_type(file_path)
                    domain = classify_business_domain(rel_path)
                    file_id = f"file_{uuid.uuid4().hex[:12]}"

                    # Generate brief plain summary placeholder
                    plain_summary = f"Provides {domain.lower()} logic for the application."

                    await db.execute(
                        """
                        INSERT INTO files (id, project_id, relative_path, file_type, language, size_bytes, plain_summary, business_domain)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (file_id, project_id, rel_path, file_type, language, size, plain_summary, domain),
                    )

                    # Extract deterministic symbols
                    parser = get_parser_for_file(rel_path, content)
                    if parser:
                        symbols = parser.parse(content, rel_path)
                        for sym in symbols:
                            sym_id = f"sym_{uuid.uuid4().hex[:12]}"
                            await db.execute(
                                """
                                INSERT INTO symbols (id, file_id, name, symbol_type, start_line, end_line, signature, parameters_json)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (sym_id, file_id, sym.name, sym.symbol_type, sym.start_line, sym.end_line, sym.signature, str(sym.parameters)),
                            )

            await db.commit()
