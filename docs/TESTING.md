# ProtoPost — Test Suite Guide

## Setup

Install test dependencies (separate from the main runtime requirements):

```bash
pip install -r requirements-test.txt
```

Run the full suite from the project root:

```bash
pytest tests/
```

`pytest.ini` sets `asyncio_mode = auto` so async tests run without needing
`@pytest.mark.asyncio` on every function.

## Test File Overview

| File | What it covers |
|---|---|
| `tests/conftest.py` | Shared fixtures: temp database, TestClient, auth headers, sample payload, mock config |
| `tests/test_api.py` | HTTP endpoints: auth guard, payload validation, pagination correctness, traceback safety |
| `tests/test_routing.py` | RoutingEngine logic: sandbox enforcement, weighted selection distribution, smart failover chain |
| `tests/test_providers.py` | Provider mocks: Resend HTTP calls, SMTP lifecycle, Mailtrap, failover from primary to secondary |
| `tests/test_database.py` | DatabaseManager: WAL mode verification, insert and retrieve, stats accuracy, total count, pagination offset |

## Running Specific Tests

```bash
pytest tests/ -v                      # verbose output for all tests
pytest tests/test_routing.py -v       # single file
pytest -k "test_sandbox"              # match by test name
pytest -k "test_api and not auth"     # compound filter
pytest --tb=short                     # condensed tracebacks
pytest --tb=long                      # full tracebacks
```

## Generating a Coverage Report

```bash
pip install pytest-cov
pytest --cov=backend --cov-report=html
```

The HTML report is written to `htmlcov/index.html`.

## Key Test Patterns

### Async Tests

All async tests work automatically due to `asyncio_mode = auto` in `pytest.ini`.
Write async test functions normally:

```python
async def test_something():
    result = await some_async_function()
    assert result["success"] is True
```

### Mocking Resend (HTTP)

```python
from unittest.mock import patch, MagicMock, AsyncMock
from backend.providers import send_via_resend

async def test_resend_success(sample_payload, mock_provider):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": "msg_abc123"}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await send_via_resend(_payload(), mock_provider)
        assert result["success"] is True
        assert result["provider_id"] == mock_provider.id
```

### Mocking SMTP (aiosmtplib)

The `async with` context manager requires mocking both `__aenter__` and
`__aexit__`:

```python
from unittest.mock import patch, AsyncMock
from backend.providers import send_via_custom_smtp

async def test_smtp_success(sample_payload, smtp_provider):
    mock_smtp = AsyncMock()
    mock_smtp.login = AsyncMock()
    mock_smtp.send_message = AsyncMock()
    mock_smtp.__aenter__ = AsyncMock(return_value=mock_smtp)
    mock_smtp.__aexit__ = AsyncMock(return_value=False)

    with patch("aiosmtplib.SMTP", return_value=mock_smtp):
        result = await send_via_custom_smtp(sample_payload, smtp_provider)

    mock_smtp.login.assert_called_once()
    mock_smtp.send_message.assert_called_once()
    assert result["success"] is True
```

### Database Isolation

Every test that touches the database uses the `test_db` fixture from
`conftest.py`, which creates a fresh temporary SQLite file per test and
tears it down after. No test shares database state with another test.

```python
def test_insert_and_retrieve(test_db):
    from backend.models import EmailLog
    from datetime import datetime

    log = EmailLog(
        timestamp=datetime.utcnow().isoformat() + "Z",
        to_addresses='["recipient@example.com"]',
        from_address="sender@example.com",
        subject="Test",
        provider_id="resend-primary",
        provider_name="Resend",
        status="success",
        processing_time_ms=25.0,
        request_payload="{}",
        response_payload="{}",
        error_trace=None,
    )
    test_db.insert_log(log)
    logs = test_db.get_logs(limit=10, offset=0)
    assert len(logs) == 1
    assert logs[0]["status"] == "success"
```

### Testing the Pagination Total Fix

This test specifically guards against the regression where `total` returned
the page length instead of the full database count:

```python
def test_total_is_not_page_length(test_app, auth_headers):
    db = test_app["db"]
    client = test_app["client"]

    for i in range(10):
        db.insert_log(...)  # insert 10 logs

    response = client.get(
        "/api/logs?limit=3&offset=0",
        headers=auth_headers
    )
    data = response.json()
    assert data["total"] == 10   # full count
    assert len(data["logs"]) == 3  # page size
```

## What Is Not Tested

Real SMTP servers and live provider APIs (Resend, Mailtrap) are not contacted
during the test suite. All provider calls are mocked. This keeps the tests
fast, free, and runnable without credentials.

Frontend JavaScript is outside the scope of this test suite. If UI testing
is needed, Playwright is the recommended tool for end-to-end browser tests.
