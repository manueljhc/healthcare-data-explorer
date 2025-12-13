"""Data export utilities."""

import csv
import io
import json
from typing import Any


class DataExporter:
    """Exports query results to various formats."""

    @staticmethod
    def to_csv(data: list[dict], include_header: bool = True) -> str:
        """
        Convert data to CSV format.

        Args:
            data: List of dictionaries representing rows
            include_header: Whether to include column headers

        Returns:
            CSV string
        """
        if not data:
            return ""

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())

        if include_header:
            writer.writeheader()

        writer.writerows(data)
        return output.getvalue()

    @staticmethod
    def to_json(data: list[dict], indent: int = 2) -> str:
        """
        Convert data to JSON format.

        Args:
            data: List of dictionaries representing rows
            indent: JSON indentation level

        Returns:
            JSON string
        """
        return json.dumps(data, indent=indent, default=str)

    @staticmethod
    def to_markdown_table(data: list[dict], max_rows: int = 100) -> str:
        """
        Convert data to Markdown table format.

        Args:
            data: List of dictionaries representing rows
            max_rows: Maximum rows to include

        Returns:
            Markdown table string
        """
        if not data:
            return "No data"

        columns = list(data[0].keys())
        rows = data[:max_rows]

        # Build header
        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join(["---"] * len(columns)) + " |"

        # Build rows
        row_lines = []
        for row in rows:
            values = [str(row.get(col, "")) for col in columns]
            # Truncate long values
            values = [v[:50] + "..." if len(v) > 50 else v for v in values]
            row_lines.append("| " + " | ".join(values) + " |")

        result = "\n".join([header, separator] + row_lines)

        if len(data) > max_rows:
            result += f"\n\n*Showing {max_rows} of {len(data)} rows*"

        return result

    @staticmethod
    def get_summary_stats(data: list[dict]) -> dict[str, Any]:
        """
        Generate summary statistics for the data.

        Args:
            data: List of dictionaries representing rows

        Returns:
            Dictionary with summary statistics
        """
        if not data:
            return {"row_count": 0, "column_count": 0}

        columns = list(data[0].keys())

        stats = {
            "row_count": len(data),
            "column_count": len(columns),
            "columns": {},
        }

        for col in columns:
            values = [row.get(col) for row in data if row.get(col) is not None]

            col_stats = {
                "non_null_count": len(values),
                "null_count": len(data) - len(values),
            }

            # Try to compute numeric stats
            numeric_values = []
            for v in values:
                try:
                    numeric_values.append(float(v))
                except (ValueError, TypeError):
                    pass

            if numeric_values:
                col_stats["type"] = "numeric"
                col_stats["min"] = min(numeric_values)
                col_stats["max"] = max(numeric_values)
                col_stats["mean"] = sum(numeric_values) / len(numeric_values)
            else:
                col_stats["type"] = "text"
                unique_values = set(str(v) for v in values)
                col_stats["unique_count"] = len(unique_values)
                if len(unique_values) <= 10:
                    col_stats["unique_values"] = list(unique_values)

            stats["columns"][col] = col_stats

        return stats
