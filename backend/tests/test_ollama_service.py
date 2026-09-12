"""
Unit tests for Ollama Service discovery and health check logic.
"""
import pytest
from backend.app.services.ollama_service import OllamaService


def test_ollama_binary_detection():
    # If installed on the system, get_binary_path should return a valid string
    bin_path = OllamaService.get_binary_path()
    assert bin_path is None or isinstance(bin_path, str)


@pytest.mark.asyncio
async def test_ollama_status():
    status = await OllamaService.get_full_status()
    assert "installed" in status
    assert "running" in status
    assert "models" in status
    assert isinstance(status["models"], list)
