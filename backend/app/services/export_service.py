"""
CodeBridge V1 - Executive Architecture Export Engine
Compiles project summaries, business domain taxonomy, ER diagrams, and endpoint catalogs into Markdown & printable HTML.
"""
from typing import Dict, Any, List
import aiosqlite

from backend.app.config import DB_PATH
from backend.app.services.diagram_service import DiagramService
from backend.app.parsers.prisma_parser import PrismaParser
from backend.app.parsers.sql_parser import SqlParser
from backend.app.parsers.openapi_parser import OpenApiParser


class ExportService:
    """Generates standalone executive architecture briefings in Markdown and HTML."""

    @staticmethod
    async def generate_markdown_report(project_id: str) -> str:
        """Assembles a comprehensive Markdown architectural report."""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            proj = await cursor.fetchone()
            if not proj:
                raise ValueError("Project not found")

            # Domains & files
            cursor = await db.execute(
                """
                SELECT business_domain, COUNT(*) as file_count, GROUP_CONCAT(relative_path, ', ') as files
                FROM files WHERE project_id = ?
                GROUP BY business_domain ORDER BY file_count DESC
                """,
                (project_id,),
            )
            domains = await cursor.fetchall()

            # Endpoints
            cursor = await db.execute(
                """
                SELECT s.name, s.signature, f.relative_path, f.business_domain
                FROM symbols s
                JOIN files f ON s.file_id = f.id
                WHERE f.project_id = ? AND s.symbol_type = 'endpoint'
                ORDER BY f.business_domain, s.name
                """,
                (project_id,),
            )
            endpoints = await cursor.fetchall()

            # Schema files for ER diagram
            cursor = await db.execute(
                """
                SELECT id, relative_path, language
                FROM files
                WHERE project_id = ? AND (file_type = 'schema' OR language IN ('prisma', 'sql', 'openapi'))
                """,
                (project_id,),
            )
            schema_files = await cursor.fetchall()

        # Build Markdown document
        lines = [
            f"# 🏛️ CodeBridge Executive Architecture Briefing: {proj['name']}",
            f"**Source**: `{proj['source_path']}` ({proj['source_type']})  ",
            f"**Generated**: `CodeBridge V1 Architecture Studio`\n",
            "---",
            "\n## 1. Executive Summary",
            proj["executive_summary"] or "Executive summary generation pending.",
            "\n---",
            "\n## 2. Business Domain Architecture & Capabilities",
            "The codebase is categorized into the following core operational departments:\n",
        ]

        for d in domains:
            domain_name = d["business_domain"] or "General Application Logic"
            file_count = d["file_count"]
            sample_files = d["files"][:180] + "..." if len(d["files"]) > 180 else d["files"]
            lines.append(f"### {domain_name} ({file_count} files)")
            lines.append(f"- **Key Components**: `{sample_files}`\n")

        # Database Schema & ER Diagram
        if schema_files:
            lines.append("\n---")
            lines.append("\n## 3. Data Persistence & Relational Schema")
            lines.append("The database structure supporting this platform:\n")

            from pathlib import Path
            er_diagram = ""
            for sf in schema_files:
                p = Path(proj["source_path"]) / sf["relative_path"]
                if p.exists():
                    code = p.read_text(encoding="utf-8", errors="ignore")
                    if sf["language"] == "prisma":
                        models = PrismaParser().parse_schema_models(code)
                        er_diagram = DiagramService.generate_schema_er_diagram(models)
                        break
                    elif sf["language"] == "sql":
                        models = SqlParser().parse_schema_models(code)
                        er_diagram = DiagramService.generate_schema_er_diagram(models)
                        break
                    elif sf["language"] == "openapi":
                        models = OpenApiParser().parse_schema_models(code)
                        er_diagram = DiagramService.generate_schema_er_diagram(models)
                        break

            if er_diagram:
                lines.append("```mermaid")
                lines.append(er_diagram)
                lines.append("```\n")

        # API & External Endpoints Catalog
        if endpoints:
            lines.append("\n---")
            lines.append("\n## 4. API & External Workflow Catalog")
            lines.append("| HTTP Method & Path | Business Domain | Implemented In |")
            lines.append("| :--- | :--- | :--- |")
            for ep in endpoints[:30]:
                lines.append(f"| **`{ep['name']}`** | {ep['business_domain']} | `{ep['relative_path']}` |")

        lines.append("\n---\n*Report generated locally by CodeBridge Architecture Interpreter.*")
        return "\n".join(lines)

    @staticmethod
    async def generate_html_report(project_id: str) -> str:
        """Assembles a self-contained, print-to-PDF ready HTML report."""
        md_content = await ExportService.generate_markdown_report(project_id)

        # Simple standalone HTML wrapper with print stylesheet
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CodeBridge Architecture Briefing</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{startOnLoad: true, theme: 'neutral'}});</script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #1a1a1a;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        h1 {{ font-size: 2rem; color: #4338ca; border-bottom: 2px solid #e5e7eb; padding-bottom: 12px; }}
        h2 {{ font-size: 1.4rem; color: #374151; margin-top: 32px; border-bottom: 1px solid #f3f4f6; padding-bottom: 8px; }}
        h3 {{ font-size: 1.15rem; color: #4b5563; }}
        code {{ background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-size: 0.88em; font-family: ui-monospace, monospace; }}
        pre {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 0.9em; }}
        th, td {{ border: 1px solid #e5e7eb; padding: 8px 12px; text-align: left; }}
        th {{ background: #f9fafb; font-weight: 600; }}
        .header-actions {{ margin-bottom: 24px; }}
        .btn {{ background: #4f46e5; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 0.9em; }}
        @media print {{
            .no-print {{ display: none; }}
            body {{ padding: 0; color: black; }}
            h2 {{ page-break-before: always; }}
        }}
    </style>
</head>
<body>
    <div class="header-actions no-print">
        <button class="btn" onclick="window.print()">🖨️ Print / Save as PDF</button>
    </div>
    <div id="report-content">
        <pre style="white-space: pre-wrap; font-family: inherit;">{md_content}</pre>
    </div>
</body>
</html>"""
        return html
