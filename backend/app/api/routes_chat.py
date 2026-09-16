"""
CodeBridge V1 - Conversational Q&A API Route
Provides multi-turn streaming chat for non-technical stakeholders with code and file context.
"""
import json
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import aiosqlite

from backend.app.config import DB_PATH
from backend.app.services.llm_gateway import LLMGateway

router = APIRouter(prefix="/api/chat", tags=["Chat"])

CHAT_SYSTEM_PROMPT = """You are CodeBridge Technical Consultant, an empathetic and highly knowledgeable AI software architect.
Your role is to answer questions about codebases, files, functions, database schemas, and dataflows for non-technical stakeholders (Product Managers, Founders, Operations, and Business Analysts).

### Guidelines:
1. Explain technical concepts in clear, intuitive, and everyday language. Use real-world business analogies where helpful.
2. If asked about potential risks or failures (e.g. database down, network errors, third-party outages, invalid inputs), clearly outline what happens step-by-step and the operational consequences.
3. Be direct, concise, and helpful. Non-engineers should not need to decipher raw code syntax.
4. Maintain conversational context across follow-up questions.
"""


class ChatMessage(BaseModel):
    role: str  # 'user', 'assistant', 'system'
    content: str


class ChatStreamRequest(BaseModel):
    messages: List[ChatMessage]
    file_id: Optional[str] = None
    project_id: Optional[str] = None
    code_context: Optional[str] = None


@router.post("/stream")
async def stream_chat(req: ChatStreamRequest):
    """Streams conversational answers with file and code context over Server-Sent Events (SSE)."""
    if not req.messages:
        raise HTTPException(status_code=400, detail="Messages cannot be empty.")

    # 1. Fetch file context if provided
    file_info = ""
    language = ""
    if req.file_id:
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("SELECT * FROM files WHERE id = ?", (req.file_id,))
                file_row = await cursor.fetchone()
                if file_row:
                    language = file_row["language"]
                    file_info = (
                        f"Active File: {file_row['relative_path']}\n"
                        f"Language: {file_row['language']}\n"
                        f"Business Domain: {file_row['business_domain']}\n"
                        f"File Purpose: {file_row['plain_summary']}\n"
                    )
        except Exception:
            pass

    # 2. Build system message with context
    system_text = CHAT_SYSTEM_PROMPT
    if file_info or req.code_context:
        context_parts = []
        if file_info:
            context_parts.append(file_info)
        if req.code_context:
            code_block = req.code_context.strip()
            # Truncate very large code blocks to preserve context window
            if len(code_block) > 4000:
                code_block = code_block[:4000] + "\n... [truncated]"
            context_parts.append(f"Inspected Code Context:\n```{language}\n{code_block}\n```")

        system_text += "\n\n### Current Code Context:\n" + "\n".join(context_parts)

    formatted_messages = [{"role": "system", "content": system_text}]
    for msg in req.messages:
        if msg.role in ("user", "assistant", "system"):
            formatted_messages.append({"role": msg.role, "content": msg.content})

    llm = LLMGateway()

    async def event_generator():
        try:
            async for chunk in llm.stream_chat(formatted_messages):
                yield f"data: {json.dumps({'event': 'chunk', 'content': chunk})}\n\n"
        except Exception as e:
            fallback_msg = (
                f"⚠️ Unable to reach the AI model service ({str(e)}). "
                "Please verify your provider settings (Ollama / OpenAI / LM Studio) in the Settings panel."
            )
            yield f"data: {json.dumps({'event': 'chunk', 'content': fallback_msg})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
