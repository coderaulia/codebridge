"""
CodeBridge V1 - System Directory Browser API
Allows the WebUI to explore local directories and select codebases with a native-feeling folder picker.
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/system", tags=["System"])


class FolderItem(BaseModel):
    name: str
    path: str


class QuickLocation(BaseModel):
    name: str
    path: str


class BrowseDirectoryResponse(BaseModel):
    current_path: str
    parent_path: Optional[str] = None
    folders: List[FolderItem]
    quick_locations: List[QuickLocation]


@router.get("/browse-directories", response_model=BrowseDirectoryResponse)
async def browse_directories(path: Optional[str] = None):
    """Lists subdirectories in the specified path for the visual folder opener."""
    home_dir = Path.home().resolve()
    dev_dir = (home_dir / "Dev").resolve()
    cwd = Path.cwd().resolve()

    # Determine starting path
    if path and path.strip():
        target = Path(os.path.expanduser(path.strip())).resolve()
    else:
        # Default to Dev dir if it exists, otherwise home dir
        target = dev_dir if dev_dir.exists() and dev_dir.is_dir() else home_dir

    if not target.exists() or not target.is_dir():
        # Fallback to home dir
        target = home_dir

    parent_path = str(target.parent) if target != target.parent else None

    # List child directories
    folders: List[FolderItem] = []
    try:
        for entry in os.scandir(target):
            if entry.is_dir() and not entry.name.startswith("."):
                folders.append(FolderItem(name=entry.name, path=str(entry.path)))
    except PermissionError:
        pass

    folders.sort(key=lambda f: f.name.lower())

    quick_locations = [
        QuickLocation(name="Dev Folder", path=str(dev_dir if dev_dir.exists() else home_dir)),
        QuickLocation(name="User Home (~)", path=str(home_dir)),
        QuickLocation(name="CodeBridge Workspace", path=str(cwd)),
    ]

    examples_dir = cwd / "examples"
    if examples_dir.exists():
        quick_locations.append(QuickLocation(name="CodeBridge Examples", path=str(examples_dir)))

    return BrowseDirectoryResponse(
        current_path=str(target),
        parent_path=parent_path,
        folders=folders,
        quick_locations=quick_locations,
    )


@router.get("/ollama-status")
async def get_ollama_status():
    """Returns the current Ollama installation, daemon execution status, and downloaded models."""
    from backend.app.services.ollama_service import OllamaService
    return await OllamaService.get_full_status()


@router.post("/ollama-start")
async def start_ollama():
    """Triggers startup of the local Ollama daemon if not currently running."""
    from backend.app.services.ollama_service import OllamaService
    return await OllamaService.ensure_running_on_startup()
