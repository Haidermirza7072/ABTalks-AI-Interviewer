import os
import shutil
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.data_loader import init_data_stores
from app.services.session_manager import SESSION_STORE, ensure_session_dir
from app.config import settings

@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path):
    """Setup clean state before each test."""
    # Set session directory to temp directory
    test_session_dir = str(tmp_path / "sessions")
    settings.SESSION_DIR = test_session_dir
    ensure_session_dir()

    # Reset in-memory session store
    SESSION_STORE.clear()

    # Load static data stores
    init_data_stores()

    yield

    # Cleanup temp directory
    if os.path.exists(test_session_dir):
        shutil.rmtree(test_session_dir, ignore_errors=True)

@pytest.fixture
def client():
    """FastAPI TestClient instance."""
    with TestClient(app) as test_client:
        yield test_client
