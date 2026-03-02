"""
Provider-level tests.
All HTTP clients and SMTP connections are mocked — zero real network calls.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.models import AppConfig, RoutingConfig, Provider, ProviderType, EmailPayload
from backend.providers import send_via_resend, send_via_mailtrap, send_via_custom_smtp
from backend.router import RoutingEngine


# ---------------------------------------------------------------------------
# Local helpers
# ---------------------------------------------------------------------------

def _payload() -> EmailPayload:
    """Build a minimal valid EmailPayload using model_validate (alias 'from' required)."""
    return EmailPayload.model_validate({
        "to": ["recipient@example.com"],
        "from": "sender@example.com",
        "subject": "Test Subject",
        "body_text": "Hello",
    })


def _resend_provider(pid: str = "p-resend") -> Provider:
    return Provider(
        id=pid,
        name="Test Resend",
        type=ProviderType.resend,
        enabled=True,
        weight=100,
        api_key="test-resend-api-key",
    )


def _smtp_provider(pid: str = "p-smtp") -> Provider:
    return Provider(
        id=pid,
        name="Test SMTP",
        type=ProviderType.custom_smtp,
        enabled=True,
        weight=100,
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="user@example.com",
        smtp_password="secret",
        smtp_use_tls=True,
        smtp_use_ssl=False,
    )


def _mailtrap_provider(pid: str = "p-mailtrap") -> Provider:
    return Provider(
        id=pid,
        name="Test Mailtrap",
        type=ProviderType.mailtrap,
        enabled=True,
        weight=100,
        api_key="test-mailtrap-api-key",
    )


def _mock_httpx(status: int, json_body: dict):
    """Return a patched httpx.AsyncClient whose POST returns the given status/json."""
    mock_response = MagicMock()
    mock_response.status_code = status
    mock_response.json.return_value = json_body
    mock_response.text = str(json_body)

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


def _mock_smtp():
    """Return an aiosmtplib.SMTP-compatible async context manager mock."""
    smtp = AsyncMock()
    smtp.login = AsyncMock()
    smtp.send_message = AsyncMock()
    smtp.connect = AsyncMock()  # must remain uncalled in send_via_custom_smtp
    smtp.__aenter__ = AsyncMock(return_value=smtp)
    smtp.__aexit__ = AsyncMock(return_value=False)
    return smtp


def _engine_patches(config: AppConfig, captured_logs: list | None = None):
    """
    Return a context-manager stack that patches router module globals for
    direct RoutingEngine.route() calls (not through TestClient).
    captured_logs, if provided, is a list that insert_log side-effects append to.
    """
    mock_db = MagicMock()

    if captured_logs is not None:
        def _capture(log):
            captured_logs.append(log)

        mock_db.insert_log = MagicMock(side_effect=_capture)
    else:
        mock_db.insert_log = MagicMock()

    return (
        patch("backend.router.config_manager.load", AsyncMock(return_value=config)),
        patch("backend.router.database_manager", mock_db),
        mock_db,
    )


# ===========================================================================
# Resend Provider Tests
# ===========================================================================

class TestResendProvider:
    async def test_resend_success_returns_success_dict(self):
        """send_via_resend returns success dict + provider id when API returns 201."""
        provider = _resend_provider()
        mock_client = _mock_httpx(201, {"id": "abc123"})

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await send_via_resend(_payload(), provider)

        assert result["success"] is True
        assert result["provider_id"] == provider.id

    async def test_resend_logs_success_in_database(self):
        """
        A successful Resend delivery writes exactly one log entry with
        status='success' to the database via the routing engine.
        """
        provider = _resend_provider()
        config = AppConfig(
            providers=[provider],
            routing=RoutingConfig(mode="manual", sandbox=False),
            version=1,
        )
        captured_logs = []
        cm_load, cm_db, mock_db = _engine_patches(config, captured_logs)
        mock_client = _mock_httpx(201, {"id": "msg-001"})

        with cm_load, cm_db, patch("httpx.AsyncClient", return_value=mock_client):
            await RoutingEngine.route(_payload())

        assert mock_db.insert_log.call_count == 1
        inserted_log = captured_logs[0]
        assert inserted_log.status == "success"

    async def test_resend_500_raises_exception(self):
        """send_via_resend raises an Exception when the API returns 500."""
        provider = _resend_provider()
        mock_client = _mock_httpx(500, {"error": "Internal Server Error"})

        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(Exception):
                await send_via_resend(_payload(), provider)

    async def test_resend_failover_to_secondary(self):
        """
        In smart mode, when the primary Resend provider returns 500, the
        engine falls back to the secondary and ultimately succeeds.
        """
        prov_primary = _resend_provider("p-primary")
        prov_secondary = _resend_provider("p-secondary")
        prov_secondary.weight = 60
        # smart mode: sorted desc by weight — give primary higher weight
        prov_primary.weight = 90
        prov_secondary.weight = 10

        config = AppConfig(
            providers=[prov_primary, prov_secondary],
            routing=RoutingConfig(mode="smart", sandbox=False),
            version=1,
        )

        call_count = {"n": 0}

        async def selective_httpx(*args, **kwargs):
            # First POST (primary) returns 500; second (secondary) returns 201
            call_count["n"] += 1
            mock_response = MagicMock()
            if call_count["n"] == 1:
                mock_response.status_code = 500
                mock_response.text = "error"
                mock_response.json.return_value = {}
            else:
                mock_response.status_code = 201
                mock_response.json.return_value = {"id": "msg-secondary"}
                mock_response.text = ""
            return mock_response

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=selective_httpx)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        cm_load, cm_db, _ = _engine_patches(config)
        with cm_load, cm_db, patch("httpx.AsyncClient", return_value=mock_client):
            result = await RoutingEngine.route(_payload())

        assert result["status"] == "success"
        assert call_count["n"] == 2  # both providers were attempted in order


# ===========================================================================
# Custom SMTP Tests
# ===========================================================================

class TestCustomSMTP:
    async def test_smtp_success_sends_message(self):
        """send_via_custom_smtp completes successfully and calls send_message once."""
        provider = _smtp_provider()
        mock_smtp = _mock_smtp()

        with patch("aiosmtplib.SMTP", return_value=mock_smtp):
            result = await send_via_custom_smtp(_payload(), provider)

        mock_smtp.send_message.assert_called_once()
        assert result["success"] is True

    async def test_smtp_timeout_captured_in_error_trace(self):
        """
        When SMTP setup raises asyncio.TimeoutError, the failure log written
        to the database must have a non-empty error_trace and status 'failed'.
        """
        provider = _smtp_provider()
        config = AppConfig(
            providers=[provider],
            routing=RoutingConfig(mode="manual", sandbox=False),
            version=1,
        )
        captured_logs = []
        cm_load, cm_db, _ = _engine_patches(config, captured_logs)

        # aiosmtplib.SMTP().__aenter__ raises TimeoutError → triggers except block
        mock_smtp = AsyncMock()
        mock_smtp.__aenter__ = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_smtp.__aexit__ = AsyncMock(return_value=False)

        from fastapi import HTTPException as FastAPIHTTPException

        with cm_load, cm_db, patch("aiosmtplib.SMTP", return_value=mock_smtp):
            with pytest.raises(FastAPIHTTPException):
                await RoutingEngine.route(_payload())

        # The failure log must carry the error trace
        assert len(captured_logs) == 1
        failure_log = captured_logs[0]
        assert failure_log.status == "failed"
        assert failure_log.error_trace is not None
        assert len(failure_log.error_trace) > 0

    async def test_smtp_no_double_connect(self):
        """
        send_via_custom_smtp must NOT call .connect() explicitly.
        The 'async with aiosmtplib.SMTP(...)' block handles the connection.
        """
        provider = _smtp_provider()
        mock_smtp = _mock_smtp()

        with patch("aiosmtplib.SMTP", return_value=mock_smtp):
            await send_via_custom_smtp(_payload(), provider)

        mock_smtp.connect.assert_not_called()


# ===========================================================================
# Mailtrap Tests
# ===========================================================================

class TestMailtrapProvider:
    async def test_mailtrap_success(self):
        """send_via_mailtrap returns success when API responds with 200."""
        provider = _mailtrap_provider()
        mock_client = _mock_httpx(200, {"success": True, "message_ids": ["m-001"]})

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await send_via_mailtrap(_payload(), provider)

        assert result["success"] is True

    async def test_mailtrap_auth_failure(self):
        """send_via_mailtrap raises an Exception when the API returns 401."""
        provider = _mailtrap_provider()
        mock_client = _mock_httpx(401, {"error": "Unauthorized"})

        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(Exception):
                await send_via_mailtrap(_payload(), provider)
