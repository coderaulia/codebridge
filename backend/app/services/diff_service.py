"""
CodeBridge V1 - Git Diff & Pull Request Translation Engine
Translates cryptic git code diffs into executive-level release notes, user impact, and risk assessments.
"""
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from backend.app.services.llm_gateway import LLMGateway

DIFF_SYSTEM_PROMPT = """You are CodeBridge Release Architect, an AI communicator who translates code diffs and Pull Requests into crystal-clear executive release notes for Product Managers, Founders, and non-technical stakeholders.

### Core Rules:
1. NEVER output raw diff syntax (+ or - code lines).
2. Always format your analysis strictly into these 4 exact markdown sections:
### 1. Executive Summary of Changes
(What was added, modified, or removed, explained in business terms)

### 2. User-Facing Feature Impact
(How end-users, customers, or workflows are affected)

### 3. Database Schema & Migration Changes
(Any new database fields, tables, foreign keys, or "No database schema changes detected")

### 4. Business & Risk Assessment
(Risk Rating: LOW, MEDIUM, or HIGH with 2-3 bullet points explaining potential business or operational risks)
"""


class DiffFileChange(BaseModel):
    file_path: str
    change_type: str = Field(..., description="'added', 'modified', 'deleted'")
    lines_added: int
    lines_deleted: int
    is_schema: bool = False


class DiffAnalysisResult(BaseModel):
    summary: str
    user_impact: str
    database_impact: str
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    risk_notes: str
    files_changed: List[DiffFileChange]
    raw_markdown: str


class DiffService:
    """Extracts and translates git diffs into plain-English executive release briefs."""

    def __init__(self, llm_gateway: Optional[LLMGateway] = None):
        self.llm = llm_gateway or LLMGateway()

    @staticmethod
    def parse_diff_structure(diff_text: str) -> List[DiffFileChange]:
        """Parses unified diff format to extract touched files and line stats."""
        changes: List[DiffFileChange] = []
        current_file: Optional[str] = None
        added = 0
        deleted = 0
        is_schema = False

        for line in diff_text.splitlines():
            if line.startswith("diff --git"):
                if current_file:
                    changes.append(
                        DiffFileChange(
                            file_path=current_file,
                            change_type="modified",
                            lines_added=added,
                            lines_deleted=deleted,
                            is_schema=is_schema,
                        )
                    )
                parts = line.split()
                # 'diff --git a/path b/path' -> take b/path
                current_file = parts[-1].replace("b/", "").strip() if len(parts) >= 4 else "unknown"
                added = 0
                deleted = 0
                is_schema = any(k in current_file.lower() for k in ("schema", "migration", ".prisma", ".sql"))
            elif line.startswith("+") and not line.startswith("+++"):
                added += 1
            elif line.startswith("-") and not line.startswith("---"):
                deleted += 1

        if current_file:
            changes.append(
                DiffFileChange(
                    file_path=current_file,
                    change_type="modified",
                    lines_added=added,
                    lines_deleted=deleted,
                    is_schema=is_schema,
                )
            )

        return changes

    @staticmethod
    def get_local_git_diff(repo_path: str) -> str:
        """Retrieves live git diff (unstaged and staged) from a local git repository."""
        path = Path(repo_path).resolve()
        if not (path / ".git").exists():
            return ""

        try:
            # Check staged + unstaged changes
            res = subprocess.run(
                ["git", "diff", "HEAD"],
                cwd=str(path),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if res.stdout.strip():
                return res.stdout

            # Fallback to unstaged working tree diff
            res_unstaged = subprocess.run(
                ["git", "diff"],
                cwd=str(path),
                capture_output=True,
                text=True,
                timeout=10,
            )
            return res_unstaged.stdout
        except Exception:
            return ""

    async def translate_diff(self, diff_text: str, project_name: str = "") -> DiffAnalysisResult:
        """Translates diff into executive 4-part release summary."""
        file_changes = self.parse_diff_structure(diff_text)
        has_schema = any(f.is_schema for f in file_changes)
        total_added = sum(f.lines_added for f in file_changes)
        total_deleted = sum(f.lines_deleted for f in file_changes)

        file_list_overview = "\n".join(
            [f"- `{f.file_path}` (+{f.lines_added}, -{f.lines_deleted})" for f in file_changes[:15]]
        )

        user_prompt = f"""Repository: {project_name or 'Current Application'}
Files Changed ({len(file_changes)} files, +{total_added}/-{total_deleted} lines):
{file_list_overview}

Diff Content (truncated for review):
```diff
{diff_text[:6000]}
```

Analyze this diff and produce the 4-part executive release notes in plain English."""

        messages = [
            {"role": "system", "content": DIFF_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response_text = await self.llm.complete_chat(messages)
        except Exception:
            # Fallback deterministic summary
            risk_level = "HIGH" if has_schema or total_added > 500 else ("MEDIUM" if total_added > 100 else "LOW")
            response_text = (
                f"### 1. Executive Summary of Changes\n"
                f"This change updates {len(file_changes)} files with +{total_added} additions and -{total_deleted} deletions.\n\n"
                f"### 2. User-Facing Feature Impact\n"
                f"- Modifies application logic across {len(file_changes)} components.\n\n"
                f"### 3. Database Schema & Migration Changes\n"
                f"{'Includes database schema or migration updates that may affect persisted records.' if has_schema else 'No database schema changes detected.'}\n\n"
                f"### 4. Business & Risk Assessment\n"
                f"Risk Rating: {risk_level}\n"
                f"- Review changes to ensure backwards compatibility across dependent workflows."
            )

        # Extract sections
        summary = self._extract_section(response_text, "1. Executive Summary", "2. User-Facing")
        impact = self._extract_section(response_text, "2. User-Facing", "3. Database")
        db_impact = self._extract_section(response_text, "3. Database", "4. Business")
        risk_notes = self._extract_section(response_text, "4. Business", None)

        risk_level = "LOW"
        if "HIGH" in risk_notes.upper() or has_schema:
            risk_level = "HIGH"
        elif "MEDIUM" in risk_notes.upper():
            risk_level = "MEDIUM"

        return DiffAnalysisResult(
            summary=summary or "Updated application components.",
            user_impact=impact or "Standard internal code refinement.",
            database_impact=db_impact or ("Schema modified" if has_schema else "No schema changes."),
            risk_level=risk_level,
            risk_notes=risk_notes or "Review recommended before deployment.",
            files_changed=file_changes,
            raw_markdown=response_text,
        )

    def _extract_section(self, text: str, start_header: str, next_header: Optional[str]) -> str:
        if start_header not in text:
            return ""
        start_idx = text.find(start_header) + len(start_header)
        if next_header and next_header in text:
            end_idx = text.find(next_header, start_idx)
            return text[start_idx:end_idx].strip("# \n\r")
        return text[start_idx:].strip("# \n\r")
