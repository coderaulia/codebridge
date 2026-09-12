"""
CodeBridge V1 - Universal OpenAI-Compatible LLM Gateway
Dynamically connects to Local Ollama, LM Studio, DeepSeek, OpenRouter, or OpenAI.
Supports streaming SSE tokens, latency diagnostics, and model discovery.
"""
import time
import json
import httpx
from typing import AsyncGenerator, Dict, Any, List, Optional
import aiosqlite
from backend.app.config import DB_PATH
from backend.app.db.models import ProviderSettings, ConnectionTestResponse


class LLMGateway:
    """Universal adapter for OpenAI-compatible LLM endpoints."""

    @staticmethod
    async def get_active_settings() -> ProviderSettings:
        """Retrieves active provider settings from the SQLite database."""
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM provider_settings WHERE id = 'active_config'")
            row = await cursor.fetchone()
            if row:
                return ProviderSettings(
                    id=row["id"],
                    provider_type=row["provider_type"],
                    base_url=row["base_url"],
                    api_key=row["api_key"] or "",
                    model_name=row["model_name"],
                    temperature=float(row["temperature"]),
                )
            return ProviderSettings(
                provider_type="ollama",
                base_url="http://localhost:11434/v1",
                api_key="",
                model_name="llama3.2",
                temperature=0.2,
            )

    @staticmethod
    async def update_settings(settings: ProviderSettings) -> None:
        """Saves new provider configurations into the database."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO provider_settings (id, provider_type, base_url, api_key, model_name, temperature, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    "active_config",
                    settings.provider_type,
                    settings.base_url.rstrip("/"),
                    settings.api_key,
                    settings.model_name,
                    settings.temperature,
                ),
            )
            await db.commit()

    @staticmethod
    async def test_connection(
        base_url: str,
        api_key: Optional[str] = "",
        model_name: Optional[str] = "",
        provider_type: Optional[str] = "custom",
    ) -> ConnectionTestResponse:
        """Sends a lightweight latency diagnostic ping to verify endpoint health and list models."""
        clean_url = base_url.rstrip("/")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        start_time = time.perf_counter()
        available_models: List[str] = []

        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Try GET /models
            try:
                models_res = await client.get(f"{clean_url}/models", headers=headers)
                if models_res.status_code == 200:
                    data = models_res.json()
                    if "data" in data and isinstance(data["data"], list):
                        available_models = [m.get("id", "") for m in data["data"] if m.get("id")]
            except Exception:
                pass

            # 2. Test lightweight completion ping
            try:
                payload = {
                    "model": model_name or (available_models[0] if available_models else "default"),
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 5,
                    "temperature": 0.0,
                }
                res = await client.post(f"{clean_url}/chat/completions", headers=headers, json=payload)
                latency = round((time.perf_counter() - start_time) * 1000, 2)

                if res.status_code in (200, 201):
                    return ConnectionTestResponse(
                        success=True,
                        latency_ms=latency,
                        message=f"Successfully connected to {clean_url} in {latency}ms",
                        available_models=available_models[:15],
                    )
                else:
                    return ConnectionTestResponse(
                        success=False,
                        latency_ms=latency,
                        message=f"Provider returned HTTP {res.status_code}: {res.text[:200]}",
                        available_models=available_models[:15],
                    )
            except Exception as e:
                latency = round((time.perf_counter() - start_time) * 1000, 2)
                return ConnectionTestResponse(
                    success=False,
                    latency_ms=latency,
                    message=f"Failed to connect to {clean_url}: {str(e)}",
                    available_models=available_models,
                )

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        override_settings: Optional[ProviderSettings] = None,
    ) -> AsyncGenerator[str, None]:
        """Streams LLM tokens chunk-by-chunk from the configured OpenAI-compatible endpoint."""
        settings = override_settings or await self.get_active_settings()
        clean_url = settings.base_url.rstrip("/")
        endpoint = f"{clean_url}/chat/completions"

        headers = {"Content-Type": "application/json"}
        if settings.api_key:
            headers["Authorization"] = f"Bearer {settings.api_key}"

        payload = {
            "model": settings.model_name,
            "messages": messages,
            "temperature": settings.temperature,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", endpoint, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    error_detail = await response.aread()
                    yield f"\n[Error: Provider returned HTTP {response.status_code}: {error_detail.decode('utf-8', errors='ignore')[:300]}]"
                    return

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            choices = chunk.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

    async def complete_chat(
        self,
        messages: List[Dict[str, str]],
        override_settings: Optional[ProviderSettings] = None,
    ) -> str:
        """Non-streaming completion for background summarization and domain classification."""
        settings = override_settings or await self.get_active_settings()
        clean_url = settings.base_url.rstrip("/")
        endpoint = f"{clean_url}/chat/completions"

        headers = {"Content-Type": "application/json"}
        if settings.api_key:
            headers["Authorization"] = f"Bearer {settings.api_key}"

        payload = {
            "model": settings.model_name,
            "messages": messages,
            "temperature": settings.temperature,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.post(endpoint, headers=headers, json=payload)
            if res.status_code != 200:
                raise RuntimeError(f"Provider returned HTTP {res.status_code}: {res.text[:300]}")
            data = res.json()
            return data["choices"][0]["message"]["content"]
