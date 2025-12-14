"""Unit tests for the discovery tool."""

import pytest


class TestDiscoveryTool:
    """Tests for DiscoveryTool class."""

    def test_get_database_overview(self, discovery_tool):
        """Test getting database overview."""
        overview = discovery_tool.get_database_overview()

        assert "database_type" in overview
        assert "table_count" in overview
        assert "tables" in overview
        assert overview["table_count"] >= 2
        assert "countries" in overview["tables"]
        assert "health_metrics" in overview["tables"]

    def test_get_database_overview_table_info(self, discovery_tool):
        """Test that table info contains expected fields."""
        overview = discovery_tool.get_database_overview()

        countries_info = overview["tables"]["countries"]
        assert "row_count" in countries_info
        assert "column_count" in countries_info
        assert "columns" in countries_info
        assert countries_info["row_count"] == 3
        assert countries_info["column_count"] == 4

    def test_get_table_details(self, discovery_tool):
        """Test getting detailed table information."""
        details = discovery_tool.get_table_details("countries")

        assert details["table_name"] == "countries"
        assert details["row_count"] == 3
        assert len(details["columns"]) == 4
        assert "sample_data" in details
        assert len(details["sample_data"]) <= 5

    def test_get_table_details_columns(self, discovery_tool):
        """Test that column details are correct."""
        details = discovery_tool.get_table_details("countries")

        column_names = [col["name"] for col in details["columns"]]
        assert "id" in column_names
        assert "name" in column_names
        assert "region" in column_names
        assert "population" in column_names

    def test_get_table_details_primary_key(self, discovery_tool):
        """Test that primary key is identified."""
        details = discovery_tool.get_table_details("countries")

        id_column = next(col for col in details["columns"] if col["name"] == "id")
        assert id_column["primary_key"] is True

    def test_get_column_values(self, discovery_tool):
        """Test getting distinct column values."""
        result = discovery_tool.get_column_values("countries", "region")

        assert result["table"] == "countries"
        assert result["column"] == "region"
        assert "distinct_values" in result
        assert len(result["distinct_values"]) == 2  # West Africa, East Africa

    def test_get_column_values_with_counts(self, discovery_tool):
        """Test that column values include counts."""
        result = discovery_tool.get_column_values("countries", "region")

        values = result["distinct_values"]
        west_africa = next(v for v in values if v["region"] == "West Africa")
        assert west_africa["count"] == 2  # Ghana, Nigeria

    def test_search_columns(self, discovery_tool):
        """Test searching for columns by name."""
        results = discovery_tool.search_columns("name")

        assert len(results) >= 1
        column_names = [r["column"] for r in results]
        assert "name" in column_names or "metric_name" in column_names

    def test_search_columns_partial_match(self, discovery_tool):
        """Test that partial column name matching works."""
        results = discovery_tool.search_columns("pop")

        assert len(results) >= 1
        assert any(r["column"] == "population" for r in results)

    def test_search_columns_no_match(self, discovery_tool):
        """Test searching for non-existent column."""
        results = discovery_tool.search_columns("nonexistent_column_xyz")

        assert len(results) == 0

    def test_get_schema_summary(self, discovery_tool):
        """Test getting schema summary for LLM."""
        summary = discovery_tool.get_schema_summary()

        assert isinstance(summary, str)
        assert "countries" in summary
        assert "health_metrics" in summary

    def test_get_table_details_nonexistent_table(self, discovery_tool):
        """Test handling of non-existent table."""
        with pytest.raises(Exception):
            discovery_tool.get_table_details("nonexistent_table")


class TestDiscoveryToolWithRealDB:
    """Tests using the real AHDC database."""

    @pytest.fixture
    def real_discovery_tool(self):
        """Create discovery tool with real database."""
        from database.connection import DatabaseConnection
        from tools.discovery import DiscoveryTool
        from pathlib import Path

        db_path = Path(__file__).parent.parent / "database" / "healthcare.db"
        if not db_path.exists():
            pytest.skip("Real database not available")

        db = DatabaseConnection(db_path=db_path)
        return DiscoveryTool(db)

    def test_real_db_has_expected_tables(self, real_discovery_tool):
        """Test that real database has expected tables."""
        overview = real_discovery_tool.get_database_overview()

        expected_tables = [
            "disease_burden",
            "intervention_outcomes",
            "health_system_capacity",
        ]
        for table in expected_tables:
            assert table in overview["tables"], f"Missing table: {table}"

    def test_real_db_disease_burden_columns(self, real_discovery_tool):
        """Test disease_burden table has expected columns."""
        details = real_discovery_tool.get_table_details("disease_burden")

        column_names = [col["name"] for col in details["columns"]]
        expected_columns = ["country", "cause_of_death", "deaths", "year"]
        for col in expected_columns:
            assert col in column_names, f"Missing column: {col}"
