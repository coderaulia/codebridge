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
