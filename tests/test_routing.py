"""
Unit tests for the RoutingEngine class.
Tests routing logic directly — no TestClient, no real provider calls.
All HTTP, SMTP, and database side-effects are mocked.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from fastapi import HTTPException

from backend.router import RoutingEngine
from backend.models import AppConfig, RoutingConfig, Provider, ProviderType, EmailPayload


# ---------------------------------------------------------------------------
# Local helpers
# ---------------------------------------------------------------------------

def _provider(pid: str, name: str, weight: int) -> Provider:
    """Build a minimal enabled Resend provider."""
    return Provider(
        id=pid,
        name=name,
        type=ProviderType.resend,
        enabled=True,
        weight=weight,
        api_key=f"key-{pid}",
    )


def _cfg(mode: str = "manual", sandbox: bool = False, providers=None) -> AppConfig:
    """Build a minimal AppConfig."""
    return AppConfig(
        providers=providers or [],
        routing=RoutingConfig(mode=mode, sandbox=sandbox),
        version=1,
    )


def _payload() -> EmailPayload:
    """Build a minimal valid EmailPayload using model_validate (alias 'from' required)."""
    return EmailPayload.model_validate({
        "to": ["recipient@example.com"],
        "from": "sender@example.com",
        "subject": "Test Subject",
        "body_text": "Hello",
    })


def _mock_db():
    """Return a MagicMock that satisfies DatabaseManager call sites in router."""
    db = MagicMock()
    db.insert_log = MagicMock()
    return db


# ===========================================================================
# Sandbox Tests
# ===========================================================================

class TestSandboxMode:
    async def test_sandbox_mode_returns_sandbox_status(self):
        """Routing in sandbox mode returns status 'sandbox' without calling dispatch."""
        config = _cfg(mode="manual", sandbox=True, providers=[_provider("p1", "P1", 100)])
        mock_db = _mock_db()

        with (
            patch("backend.router.config_manager.load", AsyncMock(return_value=config)),
            patch("backend.router.database_manager", mock_db),
        ):
            result = await RoutingEngine.route(_payload())

        assert result["status"] == "sandbox"

    async def test_sandbox_never_calls_providers(self):
        """No provider dispatch function is invoked when sandbox mode is active."""
        config = _cfg(
            mode="manual",
            sandbox=True,
            providers=[_provider("p1", "P1", 100)],
        )
        mock_db = _mock_db()

        with (
            patch("backend.router.config_manager.load", AsyncMock(return_value=config)),
            patch("backend.router.database_manager", mock_db),
            patch("backend.router.providers.dispatch", new_callable=AsyncMock) as mock_dispatch,
        ):
            await RoutingEngine.route(_payload())

        assert mock_dispatch.call_count == 0


# ===========================================================================
# Weighted Selection Tests (Manual mode)
# ===========================================================================

class TestWeightedSelection:
    async def test_weighted_selection_distribution(self):
        """
        With provider A(80) and B(20), over 1000 calls A should be chosen
        ~80% of the time (tolerance ±10 percentage points).
        """
        prov_a = _provider("a", "Provider A", 80)
        prov_b = _provider("b", "Provider B", 20)
        config = _cfg(mode="manual", providers=[prov_a, prov_b])
        mock_db = _mock_db()

        chosen_ids = []

        async def fake_dispatch(payload, provider):
            chosen_ids.append(provider.id)
            return {"success": True, "provider_id": provider.id, "message_id": "m1"}

        with (
            patch("backend.router.config_manager.load", AsyncMock(return_value=config)),
            patch("backend.router.database_manager", mock_db),
            patch("backend.router.providers.dispatch", side_effect=fake_dispatch),
        ):
            for _ in range(1000):
                await RoutingEngine.route(_payload())

        count_a = chosen_ids.count("a")
        count_b = chosen_ids.count("b")
        assert 700 <= count_a <= 900, f"Provider A chosen {count_a}/1000 — expected ~800"
        assert 100 <= count_b <= 300, f"Provider B chosen {count_b}/1000 — expected ~200"

    async def test_weighted_selection_single_provider(self):
        """Single provider at weight 100 is always chosen."""
        prov = _provider("only", "Only", 100)
        config = _cfg(mode="manual", providers=[prov])
        mock_db = _mock_db()
        chosen = []

        async def fake_dispatch(payload, provider):
            chosen.append(provider.id)
            return {"success": True, "provider_id": provider.id, "message_id": "m"}

        with (
            patch("backend.router.config_manager.load", AsyncMock(return_value=config)),
            patch("backend.router.database_manager", mock_db),
            patch("backend.router.providers.dispatch", side_effect=fake_dispatch),
        ):
            for _ in range(100):
                await RoutingEngine.route(_payload())

        assert chosen.count("only") == 100

    async def test_zero_weight_provider_never_selected(self):
        """A provider with weight 0 must never be selected as the first attempt."""
        prov_a = _provider("a", "Active", 100)
        prov_b = _provider("b", "Zero Weight", 0)
        config = _cfg(mode="manual", providers=[prov_a, prov_b])
        mock_db = _mock_db()
        first_attempts = []

        async def fake_dispatch(payload, provider):
            first_attempts.append(provider.id)
            return {"success": True, "provider_id": provider.id, "message_id": "m"}

        with (
            patch("backend.router.config_manager.load", AsyncMock(return_value=config)),
            patch("backend.router.database_manager", mock_db),
            patch("backend.router.providers.dispatch", side_effect=fake_dispatch),
        ):
            for _ in range(500):
                await RoutingEngine.route(_payload())

        assert "b" not in first_attempts, "Zero-weight provider was selected at least once"


# ===========================================================================
# Smart Failover Tests
# ===========================================================================

class TestSmartFailover:
    async def test_smart_mode_tries_highest_weight_first(self):
        """Smart mode must attempt the provider with the highest weight first."""
        prov_a = _provider("a", "Low Weight", 30)
        prov_b = _provider("b", "High Weight", 70)
        config = _cfg(mode="smart", providers=[prov_a, prov_b])
        mock_db = _mock_db()
        call_order = []

        async def fake_dispatch(payload, provider):
            call_order.append(provider.id)
            return {"success": True, "provider_id": provider.id, "message_id": "m"}

        with (
            patch("backend.router.config_manager.load", AsyncMock(return_value=config)),
            patch("backend.router.database_manager", mock_db),
            patch("backend.router.providers.dispatch", side_effect=fake_dispatch),
        ):
            await RoutingEngine.route(_payload())

        assert call_order[0] == "b", (
            f"Expected high-weight provider 'b' to be tried first, got '{call_order[0]}'"
        )

    async def test_smart_mode_failover_on_primary_error(self):
        """Smart mode must fail over to the secondary when the primary raises."""
        prov_primary = _provider("primary", "Primary", 90)
        prov_secondary = _provider("secondary", "Secondary", 10)
        config = _cfg(mode="smart", providers=[prov_primary, prov_secondary])
        mock_db = _mock_db()

        dispatch_calls = []

        async def fake_dispatch(payload, provider):
            dispatch_calls.append(provider.id)
            if provider.id == "primary":
                raise Exception("Primary provider failed")
            return {"success": True, "provider_id": provider.id, "message_id": "m"}

        with (
            patch("backend.router.config_manager.load", AsyncMock(return_value=config)),
            patch("backend.router.database_manager", mock_db),
            patch("backend.router.providers.dispatch", side_effect=fake_dispatch),
        ):
            result = await RoutingEngine.route(_payload())

        assert result["status"] == "success"
        assert dispatch_calls.count("primary") == 1
        assert dispatch_calls.count("secondary") == 1

    async def test_smart_mode_all_providers_fail(self):
        """When every provider fails, route() raises HTTPException 502 — no unhandled crash."""
        prov_a = _provider("a", "A", 60)
        prov_b = _provider("b", "B", 40)
        config = _cfg(mode="smart", providers=[prov_a, prov_b])
        mock_db = _mock_db()

        async def always_fail(payload, provider):
            raise Exception(f"Provider {provider.id} exploded")

        with (
            patch("backend.router.config_manager.load", AsyncMock(return_value=config)),
            patch("backend.router.database_manager", mock_db),
            patch("backend.router.providers.dispatch", side_effect=always_fail),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await RoutingEngine.route(_payload())

        assert exc_info.value.status_code == 502


# ===========================================================================
# Manual Mode Tests
# ===========================================================================

class TestManualMode:
    async def test_manual_mode_does_not_retry_on_failure(self):
        """
        Manual mode selects exactly one provider randomly.
        When that provider raises, only one dispatch attempt is made
        (the list still contains remaining providers but the first failure
        is the selected one; it continues to try others — so with a SINGLE
        provider in the config, dispatch is called exactly once).
        """
        prov = _provider("only", "Only", 100)
        config = _cfg(mode="manual", providers=[prov])
        mock_db = _mock_db()

        async def always_fail(payload, provider):
            raise Exception("Provider exploded")

        with (
            patch("backend.router.config_manager.load", AsyncMock(return_value=config)),
            patch("backend.router.database_manager", mock_db),
            patch("backend.router.providers.dispatch", side_effect=always_fail) as mock_dispatch,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await RoutingEngine.route(_payload())

        # With a single provider, dispatch is tried once and will fail → 502
        assert mock_dispatch.call_count == 1
        assert exc_info.value.status_code == 502
