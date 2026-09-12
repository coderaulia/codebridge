"""
CodeBridge V1 - Translation Streaming API Route
Streams real-time 4-part non-technical explanations and Mermaid diagrams via Server-Sent Events (SSE).
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.app.db.models import TranslationRequest
from backend.app.services.translation_service import TranslationService

router = APIRouter(prefix="/api/translate", tags=["Translation"])


@router.post("/stream")
async def stream_translation(req: TranslationRequest):
    """Streams token-by-token plain-English translations and validated Mermaid diagrams."""
    service = TranslationService()

    async def event_generator():
        async for sse_event in service.stream_translation(
            file_id=req.file_id,
            start_line=req.start_line,
            end_line=req.end_line,
            selected_code=req.selected_code,
        ):
            yield sse_event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
