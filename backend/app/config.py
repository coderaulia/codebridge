"""
CodeBridge V1 - Application Configuration
Centralizes configuration for storage directories, database paths, and default provider settings.
"""
from pathlib import Path
from pydantic import BaseModel

import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPOS_DIR = DATA_DIR / "repos"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPOS_DIR.mkdir(parents=True, exist_ok=True)


def get_db_path() -> Path:
    env_path = os.getenv("CODEBRIDGE_DB_PATH")
    if env_path:
        return Path(env_path).resolve()
    return DATA_DIR / "codebridge.db"


class _DynamicDbPath:
    """Dynamic path proxy so DB_PATH can be redirected during test suites without polluting production data."""
    def __fspath__(self) -> str:
        return str(get_db_path())

    def __str__(self) -> str:
        return str(get_db_path())

    def __repr__(self) -> str:
        return repr(get_db_path())

    def __getattr__(self, name: str):
        return getattr(get_db_path(), name)


DB_PATH = _DynamicDbPath()


class ProviderDefaults(BaseModel):
    provider_type: str = "ollama"
    base_url: str = "http://localhost:11434/v1"
    api_key: str = ""
    model_name: str = "llama3.2"
    temperature: float = 0.2


DEFAULT_PROVIDER = ProviderDefaults()
