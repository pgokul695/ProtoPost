"""
SQLite database manager for email logs.
Uses WAL mode for concurrent read access during high throughput.
"""

import os
import sqlite3
import sys
import threading
from datetime import datetime
from pathlib import Path
from .models import EmailLog


class DatabaseManager:
    """
    Manages the SQLite database for email delivery logs.
    Thread-safe with WAL journal mode for concurrent reads.
    """
    
    def __init__(self, db_path: str = "./emails.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._connection = None
        self._write_lock = threading.Lock()
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get or create the database connection.
        
        Returns:
            sqlite3.Connection: Database connection
        """
        if self._connection is None:
            self._connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0
            )
            self._connection.row_factory = sqlite3.Row
            # Enable WAL mode for concurrent reads
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA synchronous=NORMAL")
        return self._connection
    
    def initialize(self) -> None:
        """
        Create database schema if it doesn't exist.
        Called at application startup.
        """
        conn = self._get_connection()
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS email_logs (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            to_addresses TEXT NOT NULL,
            from_address TEXT NOT NULL,
            subject TEXT NOT NULL,
            provider_id TEXT,
            provider_name TEXT,
            status TEXT NOT NULL CHECK(status IN ('success', 'failed', 'sandbox')),
            processing_time_ms REAL NOT NULL,
            request_payload TEXT NOT NULL,
            response_payload TEXT NOT NULL,
            error_trace TEXT
        )
        """
        
        conn.execute(create_table_sql)
        
        # Create indexes for common queries
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON email_logs(timestamp DESC)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_status 
            ON email_logs(status)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_provider_id 
            ON email_logs(provider_id)
        """)
        
        conn.commit()
    
    def insert_log(self, log: EmailLog) -> None:
        """
        Insert a new email log entry.
        
        Args:
            log: EmailLog object to insert
        """
        conn = self._get_connection()
        
        with self._write_lock:
            conn.execute("""
                INSERT INTO email_logs (
                    id, timestamp, to_addresses, from_address, subject,
                    provider_id, provider_name, status, processing_time_ms,
                    request_payload, response_payload, error_trace
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log.id,
                log.timestamp,
                log.to_addresses,
                log.from_address,
                log.subject,
                log.provider_id,
                log.provider_name,
                log.status,
                log.processing_time_ms,
                log.request_payload,
                log.response_payload,
                log.error_trace
            ))
            conn.commit()
    
    def get_logs(self, limit: int = 200, offset: int = 0) -> list[dict]:
        """
        Retrieve email logs with pagination.
        
        Args:
            limit: Maximum number of logs to return
            offset: Number of logs to skip
        
        Returns:
            list[dict]: List of log entries as dictionaries
        """
        conn = self._get_connection()
        
        cursor = conn.execute("""
            SELECT 
                id, timestamp, to_addresses, from_address, subject,
                provider_id, provider_name, status, processing_time_ms,
                request_payload, response_payload, error_trace
            FROM email_logs
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_log_by_id(self, log_id: str) -> dict | None:
        """
        Retrieve a single log entry by ID.
        
        Args:
            log_id: Unique log entry ID
        
        Returns:
            dict | None: Log entry as dictionary, or None if not found
        """
        conn = self._get_connection()
        
        cursor = conn.execute("""
            SELECT 
                id, timestamp, to_addresses, from_address, subject,
                provider_id, provider_name, status, processing_time_ms,
                request_payload, response_payload, error_trace
            FROM email_logs
            WHERE id = ?
        """, (log_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_stats(self) -> dict:
        """
        Calculate aggregate statistics across all logs.
        
        Returns:
            dict: Statistics including total counts and average processing time
        """
        conn = self._get_connection()
        
        # Get counts by status
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as total_sent,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as total_failed,
                SUM(CASE WHEN status = 'sandbox' THEN 1 ELSE 0 END) as total_sandbox,
                AVG(processing_time_ms) as avg_processing_time
            FROM email_logs
        """)
        
        row = cursor.fetchone()
        
        return {
            "total": row["total"] or 0,
            "total_sent": row["total_sent"] or 0,
            "total_failed": row["total_failed"] or 0,
            "total_sandbox": row["total_sandbox"] or 0,
            "avg_processing_time": round(row["avg_processing_time"], 2) if row["avg_processing_time"] else 0
        }
    
    def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None


# Global instance.
# Priority: DATABASE_PATH env var (Docker / cloud) → next to the running
# executable / run.py (dev and PyInstaller desktop builds, persists across launches).
_db_path = (
    os.environ.get("DATABASE_PATH")
    or os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "emails.db")
)
database_manager = DatabaseManager(_db_path)
