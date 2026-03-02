"""
Unit tests for DatabaseManager.
Every test uses a fresh in-file temp SQLite database via the test_db fixture.
No mocking — these tests exercise the real SQLite layer.
"""

import pytest
from datetime import datetime

from backend.database import DatabaseManager
from backend.models import EmailLog


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _log(**kwargs) -> EmailLog:
    """Build a minimal valid EmailLog. Keyword arguments override defaults."""
    defaults = dict(
        timestamp=datetime.utcnow().isoformat() + "Z",
        to_addresses='["recipient@example.com"]',
        from_address="sender@example.com",
        subject="Test Subject",
        provider_id="provider-abc",
        provider_name="Test Provider",
        status="success",
        processing_time_ms=25.0,
        request_payload='{"to": ["recipient@example.com"]}',
        response_payload='{"success": true}',
        error_trace=None,
    )
    defaults.update(kwargs)
    return EmailLog(**defaults)


# ===========================================================================
# WAL Mode
# ===========================================================================

class TestWALMode:
    def test_wal_mode_enabled(self, test_db):
        """Database must use WAL journal mode after initialization."""
        conn = test_db._get_connection()
        row = conn.execute("PRAGMA journal_mode").fetchone()
        assert row[0] == "wal"


# ===========================================================================
# Insert and Retrieve
# ===========================================================================

class TestInsertAndRetrieve:
    def test_insert_and_retrieve_log(self, test_db):
        """A log inserted into the DB is retrieved with all fields intact."""
        log = _log(
            subject="Hello World",
            from_address="alice@example.com",
            status="success",
        )
        test_db.insert_log(log)

        logs = test_db.get_logs(limit=10, offset=0)

        assert len(logs) == 1
        row = logs[0]
        assert row["subject"] == "Hello World"
        assert row["from_address"] == "alice@example.com"
        assert row["status"] == "success"
        assert row["timestamp"] is not None and len(row["timestamp"]) > 0

    def test_get_logs_empty_db(self, test_db):
        """get_logs on an empty database returns an empty list (no error)."""
        logs = test_db.get_logs()
        assert logs == []

    def test_log_fields_present(self, test_db):
        """A retrieved log dict must contain all expected column keys."""
        test_db.insert_log(_log())
        logs = test_db.get_logs(limit=1)
        assert len(logs) == 1
        row = logs[0]
        required_keys = {
            "id",
            "timestamp",
            "to_addresses",
            "from_address",
            "subject",
            "provider_id",
            "provider_name",
            "status",
            "processing_time_ms",
            "request_payload",
            "response_payload",
            "error_trace",
        }
        for key in required_keys:
            assert key in row, f"Missing expected key '{key}' in log dict"


# ===========================================================================
# Statistics
# ===========================================================================

class TestStatistics:
    def test_stats_accuracy(self, test_db):
        """get_stats() correctly counts success and failed logs."""
        for _ in range(5):
            test_db.insert_log(_log(status="success"))
        for _ in range(2):
            test_db.insert_log(_log(status="failed"))

        stats = test_db.get_stats()

        assert stats["total_sent"] == 5
        assert stats["total_failed"] == 2

    def test_stats_empty_db(self, test_db):
        """get_stats() on an empty database returns zeros without raising."""
        stats = test_db.get_stats()

        assert stats["total"] == 0
        assert stats["total_sent"] == 0
        assert stats["total_failed"] == 0
        assert stats["total_sandbox"] == 0
        assert stats["avg_processing_time"] == 0


# ===========================================================================
# Total Count
# ===========================================================================

class TestTotalCount:
    def test_get_total_count_matches_inserts(self, test_db):
        """get_total_count() returns the exact number of inserted rows."""
        for _ in range(7):
            test_db.insert_log(_log())

        assert test_db.get_total_count() == 7


# ===========================================================================
# Pagination
# ===========================================================================

class TestPagination:
    def test_pagination_offset_correct(self, test_db):
        """
        With 10 logs, get_logs(limit=3, offset=3) returns exactly 3 rows
        and those rows are NOT the same as the first 3 (offset is applied).
        """
        for i in range(10):
            test_db.insert_log(_log(subject=f"Subject {i:02d}"))

        first_page = test_db.get_logs(limit=3, offset=0)
        second_page = test_db.get_logs(limit=3, offset=3)

        assert len(second_page) == 3

        first_page_ids = {row["id"] for row in first_page}
        second_page_ids = {row["id"] for row in second_page}
        assert first_page_ids.isdisjoint(second_page_ids), (
            "Offset was not applied — pages overlap"
        )
