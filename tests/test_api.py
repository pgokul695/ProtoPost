"""
Integration tests for ProtoPost API endpoints.
Uses FastAPI TestClient — no real SMTP or provider calls are made.
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from backend.models import EmailLog


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_log(**kwargs) -> EmailLog:
    """Build a minimal valid EmailLog for DB insertion."""
    defaults = dict(
        timestamp=datetime.utcnow().isoformat() + "Z",
        to_addresses='["test@example.com"]',
        from_address="sender@example.com",
        subject="Test",
        provider_id="provider-primary",
        provider_name="Primary Resend",
        status="success",
        processing_time_ms=42.0,
        request_payload="{}",
        response_payload="{}",
        error_trace=None,
    )
    defaults.update(kwargs)
    return EmailLog(**defaults)


# ===========================================================================
# Auth Guard Tests
# ===========================================================================

class TestAuthGuard:
    def test_send_requires_auth(self, test_app, sample_payload):
        """POST /api/send with no auth header must return 401."""
        client = test_app["client"]
        response = client.post("/api/send", json=sample_payload)
        assert response.status_code == 401

    def test_send_rejects_wrong_token(self, test_app, sample_payload):
        """POST /api/send with wrong token must return 401."""
        client = test_app["client"]
        response = client.post(
            "/api/send",
            json=sample_payload,
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert response.status_code == 401

    def test_send_accepts_correct_token(self, test_app, sample_payload, auth_headers):
        """POST /api/send with correct bearer token returns 200 when routing succeeds."""
        client = test_app["client"]
        success_result = {
            "status": "success",
            "message": "Email sent via mock",
            "log_id": "abc-123",
            "processing_time_ms": 10.0,
        }
        with patch(
            "backend.main.routing_engine.route",
            new=AsyncMock(return_value=success_result),
        ):
            response = client.post("/api/send", json=sample_payload, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "success"


# ===========================================================================
# Payload Validation Tests
# ===========================================================================

class TestPayloadValidation:
    def test_send_missing_to_field(self, test_app, sample_payload, auth_headers):
        """Payload without 'to' must return 422; error detail must mention 'to'."""
        client = test_app["client"]
        bad_payload = {k: v for k, v in sample_payload.items() if k != "to"}
        response = client.post("/api/send", json=bad_payload, headers=auth_headers)
        assert response.status_code == 422
        body_text = json.dumps(response.json()).lower()
        assert "to" in body_text

    def test_send_missing_from_field(self, test_app, sample_payload, auth_headers):
        """Payload without 'from' must return 422."""
        client = test_app["client"]
        bad_payload = {k: v for k, v in sample_payload.items() if k != "from"}
        response = client.post("/api/send", json=bad_payload, headers=auth_headers)
        assert response.status_code == 422

    def test_send_empty_body(self, test_app, auth_headers):
        """Empty JSON payload must return 422 (required fields missing)."""
        client = test_app["client"]
        response = client.post("/api/send", json={}, headers=auth_headers)
        assert response.status_code == 422

    def test_send_invalid_email_format(self, test_app, sample_payload, auth_headers):
        """'to' containing a non-email string must return 422."""
        client = test_app["client"]
        bad_payload = {**sample_payload, "to": ["not-an-email"]}
        response = client.post("/api/send", json=bad_payload, headers=auth_headers)
        assert response.status_code == 422


# ===========================================================================
# Health Check Tests
# ===========================================================================

class TestHealthCheck:
    def test_health_returns_200(self, test_app):
        """GET /api/health must return 200."""
        client = test_app["client"]
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_reports_db_status(self, test_app):
        """GET /api/health with a healthy DB reports db_connected: true."""
        client = test_app["client"]
        response = client.get("/api/health")
        assert response.status_code == 200
        body = response.json()
        # The endpoint returns {"status": "ok", ..., "db_connected": bool}
        assert "status" in body
        assert body.get("db_connected") is True


# ===========================================================================
# Logs Endpoint Tests
# ===========================================================================

class TestLogsEndpoint:
    def test_get_logs_returns_list(self, test_app, auth_headers):
        """GET /api/logs returns all 3 inserted logs."""
        client = test_app["client"]
        db = test_app["db"]
        for i in range(3):
            db.insert_log(_make_log(subject=f"Subject {i}"))
        response = client.get("/api/logs", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert "logs" in body
        assert len(body["logs"]) == 3

    def test_get_logs_pagination(self, test_app, auth_headers):
        """GET /api/logs?limit=5&offset=0 returns exactly 5 logs; total equals 10."""
        client = test_app["client"]
        db = test_app["db"]
        for i in range(10):
            db.insert_log(_make_log(subject=f"Subject {i}"))
        response = client.get("/api/logs?limit=5&offset=0", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert len(body["logs"]) == 5
        assert body["total"] == 10

    def test_get_logs_total_is_not_page_length(self, test_app, auth_headers):
        """
        total must reflect the full dataset size, not the current page size.
        Guards against the count-vs-total pagination bug.
        """
        client = test_app["client"]
        db = test_app["db"]
        for i in range(10):
            db.insert_log(_make_log(subject=f"Subject {i}"))
        response = client.get("/api/logs?limit=3&offset=0", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 10
        assert len(body["logs"]) == 3


# ===========================================================================
# Error Handling Tests
# ===========================================================================

class TestErrorHandling:
    def test_send_internal_error_hides_traceback(
        self, test_app, sample_payload, auth_headers
    ):
        """
        When routing_engine.route raises an unexpected exception:
          - Response status must be 500.
          - The secret error message must NOT appear in the response body.
          - The word "traceback" must NOT appear in the response body.
        """
        client = test_app["client"]
        with patch(
            "backend.main.routing_engine.route",
            new=AsyncMock(side_effect=Exception("secret db path")),
        ):
            response = client.post("/api/send", json=sample_payload, headers=auth_headers)

        assert response.status_code == 500
        response_text = response.text.lower()
        assert "secret db path" not in response_text
        assert "traceback" not in response_text
