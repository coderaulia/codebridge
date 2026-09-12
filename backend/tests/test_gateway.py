"""
Unit and integration tests for CodeBridge SQLite Database and Provider Gateway
"""
import pytest
from backend.app.db.database import init_db
from backend.app.services.llm_gateway import LLMGateway
from backend.app.db.models import ProviderSettings


@pytest.mark.asyncio
async def test_database_init_and_provider_settings():
    await init_db()

    settings = await LLMGateway.get_active_settings()
    assert settings is not None
    assert settings.base_url != ""

    # Test updating settings
    new_settings = ProviderSettings(
        provider_type="deepseek",
        base_url="https://api.deepseek.com/v1",
        api_key="sk-test-key",
        model_name="deepseek-chat",
        temperature=0.3,
    )
    await LLMGateway.update_settings(new_settings)

    refreshed = await LLMGateway.get_active_settings()
    assert refreshed.provider_type == "deepseek"
    assert refreshed.model_name == "deepseek-chat"
    assert refreshed.api_key == "sk-test-key"
    assert refreshed.temperature == 0.3


@pytest.mark.asyncio
async def test_connection_test_invalid_host():
    res = await LLMGateway.test_connection(
        base_url="http://invalid-local-domain-1234.local:9999/v1",
        api_key="",
        model_name="test",
        provider_type="custom",
    )
    assert res.success is False
    assert res.latency_ms is not None
