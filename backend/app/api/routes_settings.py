"""
CodeBridge V1 - Settings & Provider Gateway API Routes
Provides endpoints to manage LLM provider configuration and test latency/connectivity.
"""
from fastapi import APIRouter, HTTPException
from backend.app.db.models import ProviderSettings, ConnectionTestRequest, ConnectionTestResponse
from backend.app.services.llm_gateway import LLMGateway

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("", response_model=ProviderSettings)
async def get_settings():
    """Returns the active provider settings from the SQLite database."""
    return await LLMGateway.get_active_settings()


@router.post("", response_model=ProviderSettings)
async def update_settings(settings: ProviderSettings):
    """Updates active provider configuration dynamically."""
    await LLMGateway.update_settings(settings)
    return await LLMGateway.get_active_settings()


@router.post("/test-connection", response_model=ConnectionTestResponse)
async def test_connection(request: ConnectionTestRequest):
    """Tests connection latency and model availability for the specified provider."""
    return await LLMGateway.test_connection(
        base_url=request.base_url,
        api_key=request.api_key,
        model_name=request.model_name,
        provider_type=request.provider_type,
    )
