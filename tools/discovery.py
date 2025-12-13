"""Database discovery tool for schema exploration."""

from typing import Any

from database.connection import DatabaseConnection


class DiscoveryTool:
    """Tool for discovering and understanding database structure."""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    def get_database_overview(self) -> dict[str, Any]:
        """
        Get a high-level overview of the database.

        Returns:
            Dictionary with database overview including tables and row counts
        """
        tables = self.db.get_table_names()
        overview = {
            "database_type": "SQLite",
            "table_count": len(tables),
            "tables": {},
        }

        for table in tables:
            row_count = self.db.get_row_count(table)
            schema = self.db.get_table_schema(table)
            overview["tables"][table] = {
                "row_count": row_count,
                "column_count": len(schema),
                "columns": [col["name"] for col in schema],
            }

        return overview

    def get_table_details(self, table_name: str) -> dict[str, Any]:
        """
        Get detailed information about a specific table.

        Args:
            table_name: Name of the table to inspect

        Returns:
            Dictionary with table details including schema and sample data
        """
        schema = self.db.get_table_schema(table_name)
        sample = self.db.get_table_sample(table_name, limit=5)
        row_count = self.db.get_row_count(table_name)

        # Get column statistics
        columns_info = []
        for col in schema:
            col_info = {
                "name": col["name"],
                "type": col["type"],
                "nullable": not col["notnull"],
                "primary_key": bool(col["pk"]),
                "default": col["dflt_value"],
            }

            # Get distinct value count for non-numeric columns
            try:
                distinct_query = f"SELECT COUNT(DISTINCT {col['name']}) as cnt FROM {table_name}"
                result = self.db.execute_query(distinct_query)
                col_info["distinct_values"] = result[0]["cnt"]
            except Exception:
                col_info["distinct_values"] = None

            columns_info.append(col_info)

        return {
            "table_name": table_name,
            "row_count": row_count,
            "columns": columns_info,
            "sample_data": sample,
        }

    def get_column_values(
        self, table_name: str, column_name: str, limit: int = 100
    ) -> dict[str, Any]:
        """
        Get distinct values for a column.

        Args:
            table_name: Name of the table
            column_name: Name of the column
            limit: Maximum distinct values to return

        Returns:
            Dictionary with column value information
        """
        query = f"""
            SELECT {column_name}, COUNT(*) as count
            FROM {table_name}
            WHERE {column_name} IS NOT NULL
            GROUP BY {column_name}
            ORDER BY count DESC
            LIMIT {limit}
        """
        results = self.db.execute_query(query)

        return {
            "table": table_name,
            "column": column_name,
            "distinct_values": results,
            "total_distinct": len(results),
        }

    def search_columns(self, search_term: str) -> list[dict[str, str]]:
        """
        Search for columns matching a term across all tables.

        Args:
            search_term: Term to search for in column names

        Returns:
            List of matching columns with table names
        """
        search_lower = search_term.lower()
        matches = []

        for table_name in self.db.get_table_names():
            schema = self.db.get_table_schema(table_name)
            for col in schema:
                if search_lower in col["name"].lower():
                    matches.append({
                        "table": table_name,
                        "column": col["name"],
                        "type": col["type"],
                    })

        return matches

    def get_schema_summary(self) -> str:
        """
        Get a formatted summary of the database schema for the LLM.

        Returns:
            Formatted string describing the database schema
        """
        overview = self.get_database_overview()

        lines = [
            "# AHDC Database Schema",
            "",
            f"Total tables: {overview['table_count']}",
            "",
        ]

        for table_name, info in overview["tables"].items():
            lines.append(f"## {table_name}")
            lines.append(f"Rows: {info['row_count']:,}")
            lines.append(f"Columns: {', '.join(info['columns'])}")
            lines.append("")

        return "\n".join(lines)

    def get_detailed_schema_for_llm(self) -> str:
        """
        Get a detailed schema description optimized for LLM understanding.

        Returns:
            Detailed schema description with sample data
        """
        tables = self.db.get_table_names()

        sections = [
            "# AHDC (Anthropic Health Data Collaborative) Database Schema",
            "",
            "This database contains global health data covering disease burden, ",
            "intervention outcomes, health system capacity, immunization coverage, ",
            "maternal & child health, and infectious disease surveillance.",
            "",
        ]

        for table_name in tables:
            details = self.get_table_details(table_name)

            sections.append(f"## Table: {table_name}")
            sections.append(f"Total rows: {details['row_count']:,}")
            sections.append("")
            sections.append("### Columns:")

            for col in details["columns"]:
                pk_marker = " (PK)" if col["primary_key"] else ""
                nullable = "nullable" if col["nullable"] else "not null"
                distinct = f", {col['distinct_values']} distinct values" if col["distinct_values"] else ""
                sections.append(
                    f"- **{col['name']}**: {col['type']} ({nullable}{pk_marker}{distinct})"
                )

            sections.append("")
            sections.append("### Sample data:")
            if details["sample_data"]:
                for i, row in enumerate(details["sample_data"][:3], 1):
                    row_str = ", ".join(f"{k}={v}" for k, v in list(row.items())[:5])
                    sections.append(f"  {i}. {row_str}...")
            sections.append("")

        return "\n".join(sections)


# Tool definitions for the Agent SDK
DISCOVERY_TOOLS = [
    {
        "name": "get_database_overview",
        "description": "Get a high-level overview of the AHDC database including all tables and their row counts. Use this first to understand what data is available.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_table_details",
        "description": "Get detailed information about a specific table including column types, constraints, and sample data. Use this to understand the structure of a table before writing queries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table to inspect",
                },
            },
            "required": ["table_name"],
        },
    },
    {
        "name": "get_column_values",
        "description": "Get distinct values for a column with their counts. Useful for understanding categorical data like countries, diseases, or age groups.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table",
                },
                "column_name": {
                    "type": "string",
                    "description": "Name of the column",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum distinct values to return (default 100)",
                    "default": 100,
                },
            },
            "required": ["table_name", "column_name"],
        },
    },
    {
        "name": "search_columns",
        "description": "Search for columns by name across all tables. Use this to find relevant columns when you're not sure which table contains the data you need.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search_term": {
                    "type": "string",
                    "description": "Term to search for in column names",
                },
            },
            "required": ["search_term"],
        },
    },
]
