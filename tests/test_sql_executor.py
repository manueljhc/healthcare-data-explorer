"""Unit tests for the SQL executor tool."""

import pytest


class TestSQLExecutorTool:
    """Tests for SQLExecutorTool class."""

    def test_execute_valid_select(self, sql_executor):
        """Test executing a valid SELECT query."""
        result = sql_executor.execute_query("SELECT * FROM countries")

        assert result["success"] is True
        assert result["row_count"] == 3
        assert "data" in result
        assert len(result["data"]) == 3

    def test_execute_query_with_where(self, sql_executor):
        """Test executing query with WHERE clause."""
        result = sql_executor.execute_query(
            "SELECT * FROM countries WHERE region = 'West Africa'"
        )

        assert result["success"] is True
        assert result["row_count"] == 2
        countries = [row["name"] for row in result["data"]]
        assert "Ghana" in countries
        assert "Nigeria" in countries

    def test_execute_query_with_aggregation(self, sql_executor):
        """Test executing query with aggregation."""
        result = sql_executor.execute_query(
            "SELECT region, COUNT(*) as count FROM countries GROUP BY region"
        )

        assert result["success"] is True
        assert result["row_count"] == 2

    def test_execute_query_with_join(self, sql_executor):
        """Test executing query with JOIN."""
        result = sql_executor.execute_query("""
            SELECT c.name, h.metric_name, h.value
            FROM countries c
            JOIN health_metrics h ON c.id = h.country_id
            WHERE h.year = 2023
        """)

        assert result["success"] is True
        assert result["row_count"] >= 1

    def test_execute_query_returns_columns(self, sql_executor):
        """Test that query result includes column names."""
        result = sql_executor.execute_query("SELECT name, region FROM countries")

        assert result["success"] is True
        assert "columns" in result
        assert "name" in result["columns"]
        assert "region" in result["columns"]

    def test_execute_query_returns_execution_time(self, sql_executor):
        """Test that query result includes execution time."""
        result = sql_executor.execute_query("SELECT * FROM countries")

        assert "execution_time_seconds" in result
        assert result["execution_time_seconds"] >= 0

    def test_execute_query_adds_limit(self, sql_executor):
        """Test that LIMIT is automatically added."""
        result = sql_executor.execute_query("SELECT * FROM countries")

        # Query should have LIMIT added
        assert "LIMIT" in result["query"]

    def test_execute_query_preserves_existing_limit(self, sql_executor):
        """Test that existing LIMIT is preserved."""
        result = sql_executor.execute_query("SELECT * FROM countries LIMIT 2")

        assert result["success"] is True
        assert result["row_count"] == 2

    def test_validate_valid_query(self, sql_executor):
        """Test validating a valid SELECT query."""
        result = sql_executor.validate_query("SELECT * FROM countries")

        assert result["is_valid"] is True
        assert "error" not in result

    def test_validate_insert_rejected(self, sql_executor):
        """Test that INSERT queries are rejected."""
        result = sql_executor.validate_query(
            "INSERT INTO countries (name) VALUES ('Test')"
        )

        assert result["is_valid"] is False
        assert "error" in result

    def test_validate_update_rejected(self, sql_executor):
        """Test that UPDATE queries are rejected."""
        result = sql_executor.validate_query(
            "UPDATE countries SET name = 'Test' WHERE id = 1"
        )

        assert result["is_valid"] is False

    def test_validate_delete_rejected(self, sql_executor):
        """Test that DELETE queries are rejected."""
        result = sql_executor.validate_query("DELETE FROM countries WHERE id = 1")

        assert result["is_valid"] is False

    def test_validate_drop_rejected(self, sql_executor):
        """Test that DROP queries are rejected."""
        result = sql_executor.validate_query("DROP TABLE countries")

        assert result["is_valid"] is False

    def test_execute_invalid_query_fails(self, sql_executor):
        """Test that invalid queries return error."""
        result = sql_executor.execute_query("DELETE FROM countries")

        assert result["success"] is False
        assert "error" in result

    def test_execute_syntax_error_fails(self, sql_executor):
        """Test that queries with syntax errors fail gracefully."""
        result = sql_executor.execute_query("SELEC * FORM countries")

        assert result["success"] is False
        assert "error" in result

    def test_get_query_history(self, sql_executor):
        """Test that query history is tracked."""
        sql_executor.execute_query("SELECT * FROM countries")
        sql_executor.execute_query("SELECT * FROM health_metrics")

        history = sql_executor.get_query_history()

        assert len(history) >= 2

    def test_export_results_csv(self, sql_executor):
        """Test exporting results to CSV."""
        results = [
            {"name": "Ghana", "population": 31000000},
            {"name": "Kenya", "population": 54000000},
        ]

        export = sql_executor.export_results(results, "csv")

        assert export["format"] == "csv"
        assert "name,population" in export["data"]
        assert "Ghana" in export["data"]

    def test_export_results_json(self, sql_executor):
        """Test exporting results to JSON."""
        results = [{"name": "Ghana", "population": 31000000}]

        export = sql_executor.export_results(results, "json")

        assert export["format"] == "json"
        assert "Ghana" in export["data"]

    def test_export_results_markdown(self, sql_executor):
        """Test exporting results to Markdown."""
        results = [{"name": "Ghana", "population": 31000000}]

        export = sql_executor.export_results(results, "markdown")

        assert export["format"] == "markdown"
        assert "|" in export["data"]  # Markdown table


class TestSQLExecutorWithCTE:
    """Tests for Common Table Expression (CTE) support."""

    def test_execute_with_cte(self, sql_executor):
        """Test executing query with WITH clause (CTE)."""
        result = sql_executor.execute_query("""
            WITH african_countries AS (
                SELECT * FROM countries WHERE region LIKE '%Africa%'
            )
            SELECT name FROM african_countries
        """)

        assert result["success"] is True
        assert result["row_count"] == 3

    def test_validate_cte_accepted(self, sql_executor):
        """Test that CTE queries are accepted."""
        result = sql_executor.validate_query("""
            WITH cte AS (SELECT * FROM countries)
            SELECT * FROM cte
        """)

        assert result["is_valid"] is True
