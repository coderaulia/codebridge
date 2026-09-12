"""
CodeBridge V1 - Application Configuration
Centralizes configuration for storage directories, database paths, and default provider settings.
"""
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPOS_DIR = DATA_DIR / "repos"
DB_PATH = DATA_DIR / "codebridge.db"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPOS_DIR.mkdir(parents=True, exist_ok=True)


class ProviderDefaults(BaseModel):
    provider_type: str = "ollama"
    base_url: str = "http://localhost:11434/v1"
    api_key: str = ""
    model_name: str = "llama3.2"
    temperature: float = 0.2


DEFAULT_PROVIDER = ProviderDefaults()
