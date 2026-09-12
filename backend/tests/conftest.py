"""
Pytest configuration for CodeBridge V1 backend tests.
Ensures an isolated temporary SQLite database is used for all tests,
preventing any dummy test projects from polluting the user's production database.
"""
import os
import tempfile
from pathlib import Path
import pytest


@pytest.fixture(autouse=True, scope="session")
def isolate_test_database():
    """Points CODEBRIDGE_DB_PATH to a temporary SQLite database for the duration of the test run."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_db_path = Path(temp_dir) / "test_codebridge.db"
        os.environ["CODEBRIDGE_DB_PATH"] = str(test_db_path)
        yield
        if "CODEBRIDGE_DB_PATH" in os.environ:
            del os.environ["CODEBRIDGE_DB_PATH"]
