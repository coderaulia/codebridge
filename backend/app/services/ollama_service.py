"""
CodeBridge V1 - Ollama Lifecycle & Health Service
Detects local Ollama installation, monitors service reachability,
and automatically launches 'ollama serve' during backend startup if not already running.
"""
import os
import shutil
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
import httpx

logger = logging.getLogger("codebridge.ollama")

COMMON_OLLAMA_PATHS = [
    "/usr/local/bin/ollama",
    "/usr/bin/ollama",
    "/bin/ollama",
    str(Path.home() / ".local" / "bin" / "ollama"),
    "/opt/homebrew/bin/ollama",
]


class OllamaService:
    _instance: Optional["OllamaService"] = None
    _spawned_process: Optional[subprocess.Popen] = None
    _default_url: str = "http://127.0.0.1:11434"

    @classmethod
    def get_instance(cls) -> "OllamaService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def get_binary_path() -> Optional[str]:
        """Locates the ollama binary on the host system."""
        found = shutil.which("ollama")
        if found:
            return found
        for p in COMMON_OLLAMA_PATHS:
            if os.path.exists(p) and os.access(p, os.X_OK):
                return p
        return None

    @classmethod
    async def is_running(cls, url: Optional[str] = None) -> bool:
        """Checks if Ollama HTTP server is responsive."""
        target_url = (url or cls._default_url).rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                res = await client.get(f"{target_url}/api/version")
                return res.status_code == 200
        except Exception:
            return False

    @classmethod
    async def get_version(cls, url: Optional[str] = None) -> Optional[str]:
        """Fetches Ollama version if running."""
        target_url = (url or cls._default_url).rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                res = await client.get(f"{target_url}/api/version")
                if res.status_code == 200:
                    data = res.json()
                    return data.get("version")
        except Exception:
            pass
        return None

    @classmethod
    async def list_models(cls, url: Optional[str] = None) -> List[str]:
        """Fetches list of downloaded models in Ollama."""
        target_url = (url or cls._default_url).rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{target_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = data.get("models", [])
                    return [m.get("name") for m in models if m.get("name")]
        except Exception:
            pass
        return []

    @classmethod
    async def get_full_status(cls, url: Optional[str] = None) -> Dict[str, Any]:
        """Returns comprehensive status dictionary about Ollama on this machine."""
        bin_path = cls.get_binary_path()
        running = await cls.is_running(url)
        version = await cls.get_version(url) if running else None
        models = await cls.list_models(url) if running else []

        return {
            "installed": bin_path is not None,
            "binary_path": bin_path,
            "running": running,
            "version": version,
            "models": models,
            "managed_by_codebridge": cls._spawned_process is not None,
        }

    @classmethod
    async def ensure_running_on_startup(cls) -> Dict[str, Any]:
        """
        Lifecycle hook called on FastAPI startup:
        1. Checks if Ollama binary is installed.
        2. If installed and not running, launches 'ollama serve' in background.
        3. Waits briefly for the server to become responsive.
        """
        bin_path = cls.get_binary_path()
        if not bin_path:
            logger.info("Ollama is not installed on this machine. Skipping local Ollama daemon startup.")
            return {
                "status": "not_installed",
                "message": "Ollama is not installed. Cloud providers or manual Ollama installation can still be used.",
            }

        running = await cls.is_running()
        if running:
            ver = await cls.get_version()
            logger.info(f"Ollama is already running and accessible at {cls._default_url} (version: {ver}).")
            return {
                "status": "already_running",
                "version": ver,
                "message": f"Ollama is active and reachable at {cls._default_url}",
            }

        logger.info(f"Ollama found at '{bin_path}' but not running. Launching 'ollama serve' daemon...")
        try:
            # Spawn 'ollama serve' process detached
            process = subprocess.Popen(
                [bin_path, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            cls._spawned_process = process
            logger.info(f"Spawned 'ollama serve' subprocess (PID: {process.pid}). Waiting for initialization...")

            # Poll for up to 5 seconds to confirm it is up
            for _ in range(10):
                await asyncio.sleep(0.5)
                if await cls.is_running():
                    ver = await cls.get_version()
                    logger.info(f"Ollama server started successfully (version: {ver}) on PID {process.pid}.")
                    return {
                        "status": "started",
                        "pid": process.pid,
                        "version": ver,
                        "message": f"Ollama daemon started successfully at {cls._default_url}",
                    }

            return {
                "status": "starting",
                "pid": process.pid,
                "message": "Ollama serve launched; still initializing...",
            }
        except Exception as ex:
            logger.error(f"Failed to launch Ollama serve process: {ex}")
            return {
                "status": "error",
                "message": f"Could not launch Ollama: {str(ex)}",
            }

    @classmethod
    def shutdown_if_spawned(cls) -> None:
        """Terminates spawned Ollama process on backend shutdown if CodeBridge launched it."""
        if cls._spawned_process:
            try:
                logger.info(f"Shutting down CodeBridge-spawned Ollama daemon (PID: {cls._spawned_process.pid})...")
                cls._spawned_process.terminate()
                try:
                    cls._spawned_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    cls._spawned_process.kill()
                logger.info("Ollama daemon stopped.")
            except Exception as ex:
                logger.warning(f"Error stopping Ollama process: {ex}")
            finally:
                cls._spawned_process = None
