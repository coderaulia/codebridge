"""
Unit tests for Chat API and Translation section parsing resilience.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.services.translation_service import TranslationService


@pytest.mark.asyncio
async def test_chat_stream_empty_messages():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/chat/stream", json={"messages": []})
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_chat_stream_mocked_llm():
    async def mock_stream(*args, **kwargs):
        yield "This is "
        yield "a helpful "
        yield "explanation."

    transport = ASGITransport(app=app)
    with patch("backend.app.services.llm_gateway.LLMGateway.stream_chat", side_effect=mock_stream):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post(
                "/api/chat/stream",
                json={
                    "messages": [{"role": "user", "content": "How does billing work?"}],
                    "code_context": "function charge() { stripe.charge(); }",
                },
            )
            assert response.status_code == 200
            content = response.text
            assert "data: " in content
            assert "[DONE]" in content
            assert "helpful" in content


def test_translation_section_extraction_variations():
    service = TranslationService()

    # Variation 1: Markdown headers with hyphens
    text1 = """
### 1. Plain-English Summary
Handles user authentication and creates session tokens.

### 2. Inputs & Parameters (What goes in)
- User email and hashed password.

### 3. Outputs & Side Effects (What happens)
- Emits a JWT and records login time.

### 4. Business Rule Tie-In (Why this matters)
- Prevents unauthorized access to customer account.
"""
    p_summary = r"(?:#+\s*)?(?:1[\.\:\-\s]+)?Plain[\s\-]English\s+Summary[:\s]*"
    p_inputs = r"(?:#+\s*)?(?:2[\.\:\-\s]+)?Inputs?\s*(?:&|and)?\s*Parameters?(?:\s*\([^)]*\))?[:\s]*"
    p_outputs = r"(?:#+\s*)?(?:3[\.\:\-\s]+)?Outputs?\s*(?:&|and)?\s*(?:Side\s+)?Effects?(?:\s*\([^)]*\))?[:\s]*"
    p_business = r"(?:#+\s*)?(?:4[\.\:\-\s]+)?Business\s*Rule(?:\s*Tie[\s\-]In)?(?:\s*\([^)]*\))?[:\s]*"

    s1 = service._extract_section(text1, p_summary, p_inputs)
    i1 = service._extract_section(text1, p_inputs, p_outputs)
    o1 = service._extract_section(text1, p_outputs, p_business)
    b1 = service._extract_section(text1, p_business, None)

    assert "Handles user authentication" in s1
    assert "User email and hashed password" in i1
    assert "Emits a JWT" in o1
    assert "Prevents unauthorized access" in b1

    # Variation 2: No numbers, bold syntax, spaces instead of hyphens
    text2 = """
**Plain English Summary:**
This component processes customer refunds.

**Inputs and Parameters:**
* Refund amount in cents.

**Outputs and Effects:**
* Calls Stripe refund API and sends notification.

**Business Rule:**
* High-value refunds require supervisor confirmation.
"""
    s2 = service._extract_section(text2, p_summary, p_inputs)
    i2 = service._extract_section(text2, p_inputs, p_outputs)
    o2 = service._extract_section(text2, p_outputs, p_business)
    b2 = service._extract_section(text2, p_business, None)

    assert "This component processes customer refunds" in s2
    assert "Refund amount in cents" in i2
    assert "Calls Stripe refund API" in o2
    assert "High-value refunds require supervisor confirmation" in b2
