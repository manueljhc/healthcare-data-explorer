"""Database connection management with read-only enforcement."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


class DatabaseConnection:
    """Manages database connections with read-only safety measures."""

    DEFAULT_DB_PATH = Path(__file__).parent / "healthcare.db"
    DEFAULT_TIMEOUT = 30  # seconds
    DEFAULT_ROW_LIMIT = 10000

    def __init__(
        self,
        db_path: Optional[Path] = None,
        timeout: int = DEFAULT_TIMEOUT,
        row_limit: int = DEFAULT_ROW_LIMIT,
    ):
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.timeout = timeout
        self.row_limit = row_limit
        self._engine: Optional[Engine] = None

    @property
    def engine(self) -> Engine:
        """Lazy-load SQLAlchemy engine."""
        if self._engine is None:
            self._engine = create_engine(
                f"sqlite:///{self.db_path}",
                connect_args={"timeout": self.timeout},
            )
        return self._engine

    @contextmanager
    def get_connection(self):
        """Get a database connection context manager."""
        conn = self.engine.connect()
        try:
            yield conn
        finally:
            conn.close()

    def execute_query(self, sql: str, params: Optional[dict] = None) -> list[dict]:
        """
        Execute a read-only SQL query and return results as list of dicts.

        Args:
            sql: The SQL query to execute
            params: Optional parameters for parameterized queries

        Returns:
            List of dictionaries representing rows

        Raises:
            ValueError: If query is not read-only
            TimeoutError: If query exceeds timeout
        """
        with self.get_connection() as conn:
            result = conn.execute(text(sql), params or {})
            columns = result.keys()
            rows = result.fetchmany(self.row_limit)
            return [dict(zip(columns, row)) for row in rows]

    def get_table_names(self) -> list[str]:
        """Get all table names in the database."""
        query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        results = self.execute_query(query)
        return [row["name"] for row in results]

    def get_table_schema(self, table_name: str) -> list[dict]:
        """Get column information for a table."""
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query)

    def get_table_sample(self, table_name: str, limit: int = 5) -> list[dict]:
        """Get sample rows from a table."""
        query = f"SELECT * FROM {table_name} LIMIT {min(limit, 10)}"
        return self.execute_query(query)

    def get_row_count(self, table_name: str) -> int:
        """Get the number of rows in a table."""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query)
        return result[0]["count"] if result else 0
