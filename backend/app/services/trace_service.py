"""
CodeBridge V1 - Cross-File Dataflow & Journey Tracing Engine
Resolves multi-file import dependencies, call hierarchies, and database relations to map end-to-end journeys.
"""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import aiosqlite

from backend.app.config import DB_PATH


class TraceHop(BaseModel):
    target_file_id: str
    target_path: str
    target_domain: str
    target_language: str
    referenced_symbols: List[str] = Field(default_factory=list)
    relationship_type: str = Field(..., description="'service', 'database', 'external', 'helper'")


class TraceResult(BaseModel):
    origin_file_id: str
    origin_path: str
    origin_domain: str
    hops: List[TraceHop] = Field(default_factory=list)
    mermaid_sequence: str = ""
    summary_context: str = ""


class TraceService:
    """Discovers cross-file connections (Controller -> Service -> Database) and builds sequence flows."""

    IMPORT_PATTERNS = [
        # TS/JS: import ... from './path' or require('./path')
        re.compile(r"(?:import\s+(?:\{([^}]+)\}|([A-Za-z0-9_$]+))\s+from\s+['\"]([^'\"]+)['\"])", re.MULTILINE),
        re.compile(r"(?:const|let|var)\s+(?:\{([^}]+)\}|([A-Za-z0-9_$]+))\s*=\s*require\(['\"]([^'\"]+)['\"]\)", re.MULTILINE),
        # Python: from path import ... or import path
        re.compile(r"from\s+([A-Za-z0-9_.]+)\s+import\s+([A-Za-z0-9_,\s*]+)", re.MULTILINE),
        re.compile(r"^import\s+([A-Za-z0-9_.]+)", re.MULTILINE),
        # Java: import ...
        re.compile(r"import\s+([A-Za-z0-9_.*]+);", re.MULTILINE),
    ]

    @staticmethod
    async def trace_file_dependencies(
        project_id: str,
        file_id: str,
        snippet: Optional[str] = None,
    ) -> TraceResult:
        """Traces outbound dependencies for a file or code selection to adjacent services and schemas."""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            # 1. Fetch origin file
            cursor = await db.execute(
                """
                SELECT f.*, p.source_path
                FROM files f
                JOIN projects p ON f.project_id = p.id
                WHERE f.id = ? AND f.project_id = ?
                """,
                (file_id, project_id),
            )
            origin_row = await cursor.fetchone()
            if not origin_row:
                return TraceResult(origin_file_id=file_id, origin_path="", origin_domain="")

            # 2. Fetch all other files in project
            cursor = await db.execute(
                "SELECT id, relative_path, business_domain, language, file_type FROM files WHERE project_id = ? AND id != ?",
                (project_id, file_id),
            )
            all_files = await cursor.fetchall()

            # 3. Fetch all symbols in project
            cursor = await db.execute(
                """
                SELECT s.name, s.symbol_type, s.file_id, f.relative_path, f.business_domain, f.language
                FROM symbols s
                JOIN files f ON s.file_id = f.id
                WHERE f.project_id = ? AND f.id != ?
                """,
                (project_id, file_id),
            )
            all_symbols = await cursor.fetchall()

        # Read content from disk if snippet is not provided
        code_to_analyze = snippet
        if not code_to_analyze:
            full_path = Path(origin_row["source_path"]) / origin_row["relative_path"]
            if full_path.exists():
                code_to_analyze = full_path.read_text(encoding="utf-8", errors="ignore")
            else:
                code_to_analyze = ""

        # Map discovered targets
        target_map: Dict[str, TraceHop] = {}

        # Scan for imported / referenced symbols
        origin_path = origin_row["relative_path"]
        origin_domain = origin_row["business_domain"] or "General Application Logic"

        for sym in all_symbols:
            sym_name = sym["name"]
            # Check for direct usage or import in code
            if len(sym_name) >= 3 and re.search(r"\b" + re.escape(sym_name) + r"\b", code_to_analyze):
                target_file_id = sym["file_id"]
                if target_file_id not in target_map:
                    rel_type = "database" if sym["symbol_type"] in ("table", "model") else "service"
                    target_map[target_file_id] = TraceHop(
                        target_file_id=target_file_id,
                        target_path=sym["relative_path"],
                        target_domain=sym["business_domain"] or "General Logic",
                        target_language=sym["language"],
                        referenced_symbols=[sym_name],
                        relationship_type=rel_type,
                    )
                else:
                    if sym_name not in target_map[target_file_id].referenced_symbols:
                        target_map[target_file_id].referenced_symbols.append(sym_name)

        # Scan for relative import paths
        for pat in TraceService.IMPORT_PATTERNS:
            for m in pat.finditer(code_to_analyze):
                matched_raw = m.group(0)
                for f in all_files:
                    f_rel = f["relative_path"]
                    f_stem = Path(f_rel).stem
                    if f_stem in matched_raw and f["id"] not in target_map:
                        rel_type = "database" if f["file_type"] == "schema" else "service"
                        target_map[f["id"]] = TraceHop(
                            target_file_id=f["id"],
                            target_path=f_rel,
                            target_domain=f["business_domain"] or "General Logic",
                            target_language=f["language"],
                            referenced_symbols=[],
                            relationship_type=rel_type,
                        )

        hops = list(target_map.values())[:4]  # Limit to top 4 cross-file hops to keep diagrams legible

        # Generate Mermaid Sequence Diagram
        mermaid_seq = TraceService._build_sequence_diagram(origin_path, origin_domain, hops)

        # Build Context Summary for LLM injection
        summary_lines = [f"Origin Component: `{origin_path}` ({origin_domain})"]
        if hops:
            summary_lines.append("Cross-File Dependencies Identified:")
            for h in hops:
                syms = f" (Symbols: {', '.join(h.referenced_symbols)})" if h.referenced_symbols else ""
                summary_lines.append(f"- **{h.target_domain}** via `{h.target_path}`{syms}")
        else:
            summary_lines.append("No external local dependencies referenced; self-contained logic.")

        return TraceResult(
            origin_file_id=file_id,
            origin_path=origin_path,
            origin_domain=origin_domain,
            hops=hops,
            mermaid_sequence=mermaid_seq,
            summary_context="\n".join(summary_lines),
        )

    @staticmethod
    def _build_sequence_diagram(origin_path: str, origin_domain: str, hops: List[TraceHop]) -> str:
        """Generates a clean Mermaid sequenceDiagram tracing user action through components to database."""
        origin_alias = "Client"
        origin_label = Path(origin_path).name

        lines = [
            "sequenceDiagram",
            "    autonumber",
            "    actor User as Stakeholder / User",
            f"    participant Entry as {origin_label} ({origin_domain})",
        ]

        participants = {"Entry": origin_label}

        for idx, h in enumerate(hops):
            p_alias = f"Hop{idx+1}"
            p_label = Path(h.target_path).name
            lines.append(f"    participant {p_alias} as {p_label} ({h.target_domain})")
            participants[p_alias] = p_label

        lines.append(f"    User->>Entry: Triggers execution in {origin_label}")

        prev_alias = "Entry"
        for idx, h in enumerate(hops):
            curr_alias = f"Hop{idx+1}"
            action = f"Delegates to {h.referenced_symbols[0]}" if h.referenced_symbols else "Calls operation"
            if h.relationship_type == "database":
                action = f"Reads / writes data via {h.referenced_symbols[0] if h.referenced_symbols else 'schema'}"
            lines.append(f"    {prev_alias}->>{curr_alias}: {action}")
            prev_alias = curr_alias

        # Return journey
        if hops:
            lines.append(f"    {prev_alias}-->>Entry: Operation result / status")
        lines.append("    Entry-->>User: Returns response / confirms action")

        return "\n".join(lines)
