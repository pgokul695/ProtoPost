"""
Shared pytest fixtures for the ProtoPost test suite.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from backend.database import DatabaseManager
from backend.models import AppConfig, RoutingConfig, Provider, ProviderType


# ---------------------------------------------------------------------------
# test_db — isolated, in-file SQLite database per test
# ---------------------------------------------------------------------------

@pytest.fixture
def test_db(tmp_path):
    """
    Yields a fresh DatabaseManager backed by a temp-file SQLite DB.
    Torn down (connection closed, file deleted) after the test.
    """
    db_file = tmp_path / "test_emails.db"
    db = DatabaseManager(str(db_file))
    db.initialize()
    yield db
    db.close()


# ---------------------------------------------------------------------------
# mock_config — AppConfig with two resend providers, manual mode
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_config():
    """
    Returns an AppConfig with:
    - sandbox: False
    - mode: "manual"
    - Provider A: weight 80, resend, enabled
    - Provider B: weight 20, resend, enabled
    auth_token is handled separately via the _AUTH_TOKEN module variable.
    """
    provider_a = Provider(
        id="provider-primary",
        name="Primary Resend",
        type=ProviderType.resend,
        enabled=True,
        weight=80,
        api_key="test-api-key-primary",
    )
    provider_b = Provider(
        id="provider-secondary",
        name="Secondary Resend",
        type=ProviderType.resend,
        enabled=True,
        weight=20,
        api_key="test-api-key-secondary",
    )
    return AppConfig(
        providers=[provider_a, provider_b],
        routing=RoutingConfig(mode="manual", sandbox=False),
        version=1,
    )


# ---------------------------------------------------------------------------
# test_app — TestClient wired to test_db and mock_config, auth enabled
# ---------------------------------------------------------------------------

@pytest.fixture
def test_app(mock_config):
    """
    Yields a dict with:
      "client" → FastAPI TestClient backed by isolated test infrastructure
      "db"     → the DatabaseManager instance used by this client

    The following module-level globals are patched for the duration of the test:
      backend.main.database_manager  → fresh DatabaseManager on tmp file
      backend.router.database_manager → same instance
      backend.main.config_manager    → AsyncMock whose .load() returns mock_config
      backend.router.config_manager  → same mock
      backend.main._AUTH_TOKEN       → "test-token"
    """
    import backend.main as main_module
    import backend.router as router_module
    from fastapi.testclient import TestClient

    # Fresh isolated database
    tmp = tempfile.mkdtemp()
    db_file = Path(tmp) / "test_app_emails.db"
    db = DatabaseManager(str(db_file))
    db.initialize()

    # Config manager mock — returns mock_config on every .load() call
    mock_cm = MagicMock()
    mock_cm.load = AsyncMock(return_value=mock_config)
    mock_cm.save = AsyncMock()
    mock_cm.save_sync = MagicMock()
    mock_cm.get_default_config = MagicMock(return_value=mock_config)

    with (
        patch.object(main_module, "database_manager", db),
        patch.object(router_module, "database_manager", db),
        patch.object(main_module, "config_manager", mock_cm),
        patch.object(router_module, "config_manager", mock_cm),
        patch("backend.main._AUTH_TOKEN", "test-token"),
    ):
        # Use TestClient as context manager so lifespan fires with patched globals.
        # The lifespan calls db.initialize() (idempotent) and mock_cm.load().
        with TestClient(main_module.app, raise_server_exceptions=False) as client:
            yield {"client": client, "db": db}

    db.close()
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# auth_headers — correct Bearer token for test_app
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_headers():
    """
    Returns headers with the Bearer token that test_app recognises.
    The token matches backend.main._AUTH_TOKEN = "test-token" patched in test_app.
    """
    return {"Authorization": "Bearer test-token"}


# ---------------------------------------------------------------------------
# sample_payload — minimal valid EmailPayload dict
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_payload():
    """
    Returns a valid EmailPayload dict that satisfies all Pydantic validators.
    Uses 'from' alias (not 'from_address') as required by the JSON API.
    """
    return {
        "to": ["recipient@example.com"],
        "from": "sender@example.com",
        "subject": "Test Subject",
        "body_text": "Test body content",
    }
