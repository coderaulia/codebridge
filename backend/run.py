"""
CodeBridge V1 - Backend Runner
Configures PYTHONPATH and app_dir so uvicorn reloader subprocesses cleanly import backend modules.
"""
import os
import sys
from pathlib import Path
import uvicorn

# Add root directory to sys.path
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Set PYTHONPATH environment variable for spawned reloader worker processes
existing_pythonpath = os.environ.get("PYTHONPATH", "")
if root_dir not in existing_pythonpath:
    os.environ["PYTHONPATH"] = f"{root_dir}:{existing_pythonpath}" if existing_pythonpath else root_dir

if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        app_dir=root_dir,
    )
