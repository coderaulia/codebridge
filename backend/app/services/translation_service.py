"""
CodeBridge V1 - Plain-English Translation Engine
Translates selected code blocks and database schemas into the 4-part non-technical breakdown with Mermaid diagrams.
"""
import hashlib
import json
from typing import AsyncGenerator, Dict, Any, Optional
import aiosqlite

from backend.app.config import DB_PATH
from backend.app.services.llm_gateway import LLMGateway
from backend.app.services.diagram_service import DiagramService
from backend.app.parsers.prisma_parser import PrismaParser
from backend.app.parsers.sql_parser import SqlParser
from backend.app.parsers.drizzle_parser import DrizzleParser
from backend.app.parsers.base import ParsedSymbol

SYSTEM_PROMPT = """You are CodeBridge Translator, an expert AI software architect who translates complex code and database schemas into crystal-clear business English for product managers, executives, and non-technical stakeholders.

### Core Rules:
1. NEVER output raw walls of uncommented code. Non-engineers should not need to decipher code syntax.
2. Translate jargon into tangible everyday concepts (e.g., instead of "mutates state via dispatch", say "updates the customer's live dashboard with their new balance").
3. Always format your explanation strictly using these 4 exact markdown headers:
### 1. Plain-English Summary
(2-3 sentences explaining what this block does in everyday terms)

### 2. Inputs & Parameters (What goes in)
(Bullet points explaining what data enters this component, using intuitive analogies)

### 3. Outputs & Side Effects (What happens)
(Bullet points explaining the direct consequences, database saves, notifications, or charges)

### 4. Business Rule Tie-In (Why this matters)
(Why this logic is crucial to the business operation, revenue generation, or security posture)

4. If relevant, include a short Mermaid diagram in ```mermaid code fence illustrating the flow or relationship."""


class TranslationService:
    """Translates highlighted code and database schemas into structured plain-English explanations."""

    def __init__(self, llm_gateway: Optional[LLMGateway] = None):
        self.llm = llm_gateway or LLMGateway()

    async def stream_translation(
        self,
        file_id: str,
        start_line: int,
        end_line: int,
        selected_code: str,
    ) -> AsyncGenerator[str, None]:
        """Streams 4-part translation tokens over SSE, checking SQLite cache first."""
        # 1. Fetch file context from DB
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM files WHERE id = ?", (file_id,))
            file_row = await cursor.fetchone()
            if not file_row:
                yield f"data: {json.dumps({'error': 'File not found'})}\n\n"
                return

            # Find matching symbol in line range
            cursor = await db.execute(
                """
                SELECT * FROM symbols
                WHERE file_id = ? AND start_line <= ? AND end_line >= ?
                LIMIT 1
                """,
                (file_id, end_line, start_line),
            )
            symbol_row = await cursor.fetchone()

        settings = await self.llm.get_active_settings()
        cache_key = hashlib.sha256(
            f"{selected_code.strip()}_{file_row['language']}_{settings.model_name}".encode("utf-8")
        ).hexdigest()

        # 2. Check cache
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM translations_cache WHERE cache_key = ?", (cache_key,))
            cached = await cursor.fetchone()
            if cached:
                cached_payload = {
                    "plain_summary": cached["summary_text"],
                    "inputs_and_parameters": cached["inputs_text"],
                    "outputs_and_effects": cached["outputs_text"],
                    "business_rule_tie_in": cached["business_rule_text"],
                    "mermaid_diagram": cached["mermaid_code"],
                    "cached": True,
                }
                yield f"data: {json.dumps({'event': 'cached', 'data': cached_payload})}\n\n"
                yield "data: [DONE]\n\n"
                return

        # 3. Generate deterministic Mermaid diagram if applicable
        mermaid_code = ""
        is_schema = file_row["file_type"] == "schema" or file_row["language"] in ("prisma", "sql")

        if is_schema:
            if file_row["language"] == "prisma":
                models = PrismaParser().parse_schema_models(selected_code)
                mermaid_code = DiagramService.generate_schema_er_diagram(models)
            elif file_row["language"] == "sql":
                models = SqlParser().parse_schema_models(selected_code)
                mermaid_code = DiagramService.generate_schema_er_diagram(models)
            elif "table" in selected_code.lower():
                models = DrizzleParser().parse_schema_models(selected_code)
                mermaid_code = DiagramService.generate_schema_er_diagram(models)
        elif symbol_row:
            sym_obj = ParsedSymbol(
                name=symbol_row["name"],
                symbol_type=symbol_row["symbol_type"],
                start_line=symbol_row["start_line"],
                end_line=symbol_row["end_line"],
                signature=symbol_row["signature"],
            )
            mermaid_code = DiagramService.generate_flowchart_from_symbols(sym_obj)

        # 4. Stream LLM translation
        user_prompt = f"""File: {file_row['relative_path']}
Language: {file_row['language']}
Business Domain: {file_row['business_domain']}
Lines: {start_line}-{end_line}

Code Block to Translate:
```{file_row['language']}
{selected_code}
```

Translate this into the 4-part CodeBridge structure in plain English. Include real-world analogies for non-technical readers."""

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        full_response = []
        try:
            async for chunk in self.llm.stream_chat(messages, override_settings=settings):
                full_response.append(chunk)
                yield f"data: {json.dumps({'event': 'chunk', 'content': chunk})}\n\n"
        except Exception as e:
            # Fallback graceful explanation if LLM is offline
            fallback_text = (
                f"### 1. Plain-English Summary\n"
                f"This component implements {file_row['business_domain'].lower()} in `{file_row['relative_path']}`.\n\n"
                f"### 2. Inputs & Parameters (What goes in)\n"
                f"- Processes input data passed to lines {start_line}–{end_line}.\n\n"
                f"### 3. Outputs & Side Effects (What happens)\n"
                f"- Executes the defined operations and returns application state.\n\n"
                f"### 4. Business Rule Tie-In (Why this matters)\n"
                f"- Vital to the product's operational capability in {file_row['business_domain']}."
            )
            full_response.append(fallback_text)
            yield f"data: {json.dumps({'event': 'chunk', 'content': fallback_text})}\n\n"

        complete_text = "".join(full_response)

        # Parse the 4 sections from complete_text
        summary_section = self._extract_section(complete_text, "1. Plain-English Summary", "2. Inputs")
        inputs_section = self._extract_section(complete_text, "2. Inputs & Parameters", "3. Outputs")
        outputs_section = self._extract_section(complete_text, "3. Outputs & Side Effects", "4. Business")
        business_section = self._extract_section(complete_text, "4. Business Rule Tie-In", None)

        # Save to SQLite cache
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT OR IGNORE INTO translations_cache (id, cache_key, summary_text, inputs_text, outputs_text, business_rule_text, mermaid_code)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"trans_{hashlib.md5(cache_key.encode()).hexdigest()[:12]}",
                    cache_key,
                    summary_section or complete_text[:250],
                    inputs_section or "Standard parameters passed to function",
                    outputs_section or "Returns computed data or modifies record",
                    business_section or "Essential to domain workflow",
                    mermaid_code,
                ),
            )
            await db.commit()

        # Emit final structured payload with mermaid diagram
        final_payload = {
            "plain_summary": summary_section or complete_text[:250],
            "inputs_and_parameters": inputs_section or "Parameters entering this block",
            "outputs_and_effects": outputs_section or "Operation results",
            "business_rule_tie_in": business_section or "Core business rule",
            "mermaid_diagram": mermaid_code,
            "raw_markdown": complete_text,
            "cached": False,
        }
        yield f"data: {json.dumps({'event': 'complete', 'data': final_payload})}\n\n"
        yield "data: [DONE]\n\n"

    def _extract_section(self, text: str, start_header: str, next_header: Optional[str]) -> str:
        """Extracts markdown text between two section headers."""
        if start_header not in text:
            return ""
        start_idx = text.find(start_header) + len(start_header)
        if next_header and next_header in text:
            end_idx = text.find(next_header, start_idx)
            return text[start_idx:end_idx].strip("# \n\r")
        return text[start_idx:].strip("# \n\r")
