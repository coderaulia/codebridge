"""
CodeBridge V1 - Hierarchical Summarization Engine
Produces bottom-up plain-English summaries at the File, Domain, and Project levels.
"""
from typing import Dict, Any, List
import aiosqlite
from backend.app.config import DB_PATH
from backend.app.services.llm_gateway import LLMGateway


class SummarizerService:
    """Bottom-up hierarchical summarizer translating technical codebases into executive briefs."""

    def __init__(self, llm_gateway: LLMGateway = None):
        self.llm = llm_gateway or LLMGateway()

    async def generate_project_executive_summary(self, project_id: str) -> str:
        """Generates an executive briefing explaining what the entire repository accomplishes."""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            # Check if summary already exists
            cursor = await db.execute("SELECT executive_summary, name FROM projects WHERE id = ?", (project_id,))
            proj_row = await cursor.fetchone()
            if not proj_row:
                raise ValueError("Project not found")

            if proj_row["executive_summary"]:
                return proj_row["executive_summary"]

            # Aggregate domain and symbol statistics
            cursor = await db.execute(
                """
                SELECT business_domain, COUNT(*) as file_count, GROUP_CONCAT(relative_path, ', ') as sample_files
                FROM files
                WHERE project_id = ?
                GROUP BY business_domain
                ORDER BY file_count DESC
                """,
                (project_id,),
            )
            domains = await cursor.fetchall()

            cursor = await db.execute(
                """
                SELECT symbol_type, COUNT(*) as sym_count
                FROM symbols s
                JOIN files f ON s.file_id = f.id
                WHERE f.project_id = ?
                GROUP BY symbol_type
                """,
                (project_id,),
            )
            symbols_stat = await cursor.fetchall()

        domain_overview = "\n".join(
            [f"- **{d['business_domain']}** ({d['file_count']} files)" for d in domains]
        )
        symbol_overview = ", ".join([f"{s['sym_count']} {s['symbol_type']}s" for s in symbols_stat])

        prompt = f"""You are CodeBridge Architect, an executive technical communicator.
Summarize the following software repository in plain, crystal-clear business English for product managers, executives, and non-technical founders:

Project Name: {proj_row['name']}
Business Domains Identified:
{domain_overview}
Key Code Symbols: {symbol_overview}

Instructions:
1. Provide a 2-paragraph Executive Overview explaining what this product accomplishes in real-world terms.
2. Outline the Top 3 Business Capabilities (e.g. User Management, Payment Processing, Notification Pipeline).
3. Do NOT use cryptic programming jargon. Explain what value this system creates.
"""
        messages = [
            {"role": "system", "content": "You are an expert enterprise architect who explains software systems to business stakeholders in plain English."},
            {"role": "user", "content": prompt},
        ]

        try:
            summary = await self.llm.complete_chat(messages)
        except Exception:
            # Fallback deterministic summary if LLM endpoint is currently offline
            summary = (
                f"### Executive Briefing: {proj_row['name']}\n\n"
                f"This repository implements an integrated software platform organized into key operational domains:\n"
                f"{domain_overview}\n\n"
                f"The system contains {symbol_overview}, powering modern API workflows, database persistence, and user interfaces."
            )

        # Cache summary in projects table
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE projects SET executive_summary = ? WHERE id = ?", (summary, project_id))
            await db.commit()

        return summary

    async def generate_file_summary(self, file_id: str) -> str:
        """Generates a 1-2 sentence non-technical summary of a file's business responsibility (Level 1)."""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM files WHERE id = ?", (file_id,))
            file_row = await cursor.fetchone()
            if not file_row:
                raise ValueError("File not found")

            # Fetch symbols for this file
            cursor = await db.execute("SELECT name, symbol_type FROM symbols WHERE file_id = ? LIMIT 8", (file_id,))
            symbols = await cursor.fetchall()

        sym_names = [s["name"] for s in symbols]
        sym_desc = f"including {', '.join(sym_names[:4])}" if sym_names else "with core operational routines"

        prompt = f"""You are CodeBridge File Analyst. Summarize this code file in 1-2 plain English sentences for a non-technical product manager:
File: {file_row['relative_path']}
Language: {file_row['language']}
Business Domain: {file_row['business_domain']}
Key Symbols: {', '.join(sym_names)}

Explain what business capability or workflow this file manages. Do not mention line numbers or code syntax."""

        messages = [
            {"role": "system", "content": "You explain code files to non-technical stakeholders in 1-2 concise sentences."},
            {"role": "user", "content": prompt},
        ]

        try:
            summary = await self.llm.complete_chat(messages)
            summary = summary.strip().strip('"')
        except Exception:
            summary = f"Implements {file_row['business_domain'].lower()} capabilities in `{file_row['relative_path']}`, {sym_desc}."

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE files SET plain_summary = ? WHERE id = ?", (summary, file_id))
            await db.commit()

        return summary

    async def generate_domain_summary(self, project_id: str, domain_name: str) -> str:
        """Generates a business capability synthesis for an entire domain grouping (Level 2)."""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT relative_path, plain_summary FROM files WHERE project_id = ? AND business_domain = ?",
                (project_id, domain_name),
            )
            files = await cursor.fetchall()

        if not files:
            return f"Manages {domain_name.lower()} operations."

        file_list = "\n".join([f"- `{f['relative_path']}`: {f['plain_summary'] or 'Operational component'}" for f in files[:8]])

        prompt = f"""You are CodeBridge Enterprise Architect. Provide a 2-sentence executive summary of what the '{domain_name}' department accomplishes in this system:
Components:
{file_list}

Explain the business purpose and value to customers or operations in clear, non-technical English."""

        messages = [
            {"role": "system", "content": "You summarize business domain capabilities for executives in 2 plain English sentences."},
            {"role": "user", "content": prompt},
        ]

        try:
            summary = await self.llm.complete_chat(messages)
            summary = summary.strip().strip('"')
        except Exception:
            summary = f"Coordinates {domain_name.lower()} across {len(files)} components, ensuring reliable workflows."

        return summary

    async def generate_project_macro_diagram(self, project_id: str) -> str:
        """Generates a macro system architecture Mermaid diagram mapping all domains in the project."""
        from backend.app.services.diagram_service import DiagramService

        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT business_domain as domain_name, COUNT(*) as file_count, GROUP_CONCAT(relative_path, ', ') as sample_files
                FROM files
                WHERE project_id = ?
                GROUP BY business_domain
                ORDER BY file_count DESC
                """,
                (project_id,),
            )
            rows = await cursor.fetchall()

        domains_data = [dict(r) for r in rows]
        return DiagramService.generate_macro_architecture_diagram(domains_data)

    async def generate_all_file_summaries(self, project_id: str) -> int:
        """Background task to generate AI file summaries for all files in a project."""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id FROM files WHERE project_id = ?",
                (project_id,),
            )
            rows = await cursor.fetchall()

        count = 0
        for r in rows:
            try:
                await self.generate_file_summary(r["id"])
                count += 1
            except Exception:
                continue
        return count
