"""SQL generation and execution tool with security validation."""

import time
from typing import Any, Optional

from database.connection import DatabaseConnection
from utils.security import SQLValidator
from utils.export import DataExporter


class SQLExecutorTool:
    """Tool for generating, validating, and executing SQL queries."""

    def __init__(
        self,
        db: DatabaseConnection,
        validator: Optional[SQLValidator] = None,
        max_rows: int = 10000,
        timeout_seconds: int = 30,
    ):
        self.db = db
        self.validator = validator or SQLValidator()
        self.max_rows = max_rows
        self.timeout_seconds = timeout_seconds
        self.query_history: list[dict] = []

    def validate_query(self, sql: str) -> dict[str, Any]:
        """
        Validate a SQL query without executing it.

        Args:
            sql: The SQL query to validate

        Returns:
            Dictionary with validation results
        """
        is_valid, error_message = self.validator.validate(sql)

        result = {
            "is_valid": is_valid,
            "query": sql,
        }

        if not is_valid:
            result["error"] = error_message

        return result

    def execute_query(self, sql: str, explain: bool = False) -> dict[str, Any]:
        """
        Execute a validated SQL query.

        Args:
            sql: The SQL query to execute
            explain: Whether to include query explanation

        Returns:
            Dictionary with query results and metadata
        """
        # Validate first
        is_valid, error_message = self.validator.validate(sql)
        if not is_valid:
            return {
                "success": False,
                "error": f"Query validation failed: {error_message}",
                "query": sql,
            }

        # Ensure LIMIT is applied
        sql_with_limit = self._ensure_limit(sql)

        start_time = time.time()

        try:
            # Execute query
            results = self.db.execute_query(sql_with_limit)
            execution_time = time.time() - start_time

            # Record in history
            self.query_history.append({
                "query": sql_with_limit,
                "row_count": len(results),
                "execution_time": execution_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            })

            response = {
                "success": True,
                "query": sql_with_limit,
                "row_count": len(results),
                "data": results,
                "execution_time_seconds": round(execution_time, 3),
            }

            # Add summary stats
            if results:
                response["columns"] = list(results[0].keys())
                response["summary"] = DataExporter.get_summary_stats(results)

            return response

        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "query": sql_with_limit,
                "execution_time_seconds": round(execution_time, 3),
            }

    def _ensure_limit(self, sql: str) -> str:
        """Ensure the query has a LIMIT clause."""
        sql_upper = sql.upper().strip()

        # Check if LIMIT already exists
        if "LIMIT" in sql_upper:
            return sql

        # Add LIMIT
        if sql.rstrip().endswith(";"):
            return sql.rstrip()[:-1] + f" LIMIT {self.max_rows};"
        else:
            return sql + f" LIMIT {self.max_rows}"

    def get_query_history(self, limit: int = 10) -> list[dict]:
        """Get recent query history."""
        return self.query_history[-limit:]

    def export_results(
        self, results: list[dict], format: str = "csv"
    ) -> dict[str, Any]:
        """
        Export query results to specified format.

        Args:
            results: Query results to export
            format: Export format (csv, json, markdown)

        Returns:
            Dictionary with exported data
        """
        if format == "csv":
            exported = DataExporter.to_csv(results)
            mime_type = "text/csv"
            filename = "query_results.csv"
        elif format == "json":
            exported = DataExporter.to_json(results)
            mime_type = "application/json"
            filename = "query_results.json"
        elif format == "markdown":
            exported = DataExporter.to_markdown_table(results)
            mime_type = "text/markdown"
            filename = "query_results.md"
        else:
            return {"error": f"Unsupported format: {format}"}

        return {
            "format": format,
            "mime_type": mime_type,
            "filename": filename,
            "data": exported,
            "row_count": len(results),
        }


# Tool definitions for the Agent SDK
SQL_EXECUTOR_TOOLS = [
    {
        "name": "validate_sql",
        "description": "Validate a SQL query for security and correctness WITHOUT executing it. Use this to check if a query is safe before running it. Returns validation status and any errors.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "The SQL query to validate",
                },
            },
            "required": ["sql"],
        },
    },
    {
        "name": "execute_sql",
        "description": "Execute a read-only SQL query against the AHDC database. The query will be validated for security first. Returns the query results with metadata. IMPORTANT: Only SELECT queries are allowed. All queries are automatically limited to 10,000 rows.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "The SQL query to execute (must be a SELECT query)",
                },
            },
            "required": ["sql"],
        },
    },
    {
        "name": "export_results",
        "description": "Export query results to a downloadable format (CSV, JSON, or Markdown).",
        "input_schema": {
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "description": "The query results to export",
                    "items": {"type": "object"},
                },
                "format": {
                    "type": "string",
                    "enum": ["csv", "json", "markdown"],
                    "description": "Export format",
                    "default": "csv",
                },
            },
            "required": ["results"],
        },
    },
]
