"""SQL validation and security utilities."""

import re
from typing import Tuple


class SQLValidator:
    """Validates SQL queries for security and read-only enforcement."""

    # Dangerous SQL keywords that indicate write operations
    WRITE_KEYWORDS = [
        r"\bINSERT\b",
        r"\bUPDATE\b",
        r"\bDELETE\b",
        r"\bDROP\b",
        r"\bCREATE\b",
        r"\bALTER\b",
        r"\bTRUNCATE\b",
        r"\bREPLACE\b",
        r"\bMERGE\b",
        r"\bGRANT\b",
        r"\bREVOKE\b",
        r"\bEXEC\b",
        r"\bEXECUTE\b",
        r"\bCALL\b",
    ]

    # Patterns that might indicate SQL injection attempts
    INJECTION_PATTERNS = [
        r";\s*--",  # Comment after semicolon
        r";\s*/\*",  # Block comment after semicolon
        r"UNION\s+ALL\s+SELECT",  # Union-based injection
        r"'\s*OR\s+'1'\s*=\s*'1",  # Classic OR injection
        r"'\s*OR\s+1\s*=\s*1",  # Numeric OR injection
        r"--\s*$",  # Trailing comment
        r";\s*DROP\b",  # Drop after semicolon
        r"WAITFOR\s+DELAY",  # Time-based injection
        r"BENCHMARK\s*\(",  # MySQL benchmark
        r"SLEEP\s*\(",  # Sleep function
        r"pg_sleep",  # PostgreSQL sleep
    ]

    # Allowed SQL keywords for read operations
    ALLOWED_KEYWORDS = [
        "SELECT",
        "FROM",
        "WHERE",
        "JOIN",
        "LEFT",
        "RIGHT",
        "INNER",
        "OUTER",
        "CROSS",
        "ON",
        "AND",
        "OR",
        "NOT",
        "IN",
        "BETWEEN",
        "LIKE",
        "IS",
        "NULL",
        "ORDER",
        "BY",
        "ASC",
        "DESC",
        "LIMIT",
        "OFFSET",
        "GROUP",
        "HAVING",
        "DISTINCT",
        "AS",
        "CASE",
        "WHEN",
        "THEN",
        "ELSE",
        "END",
        "CAST",
        "COALESCE",
        "COUNT",
        "SUM",
        "AVG",
        "MIN",
        "MAX",
        "ROUND",
        "UPPER",
        "LOWER",
        "SUBSTR",
        "LENGTH",
        "TRIM",
        "DATE",
        "YEAR",
        "MONTH",
        "DAY",
        "WITH",
        "UNION",
        "EXCEPT",
        "INTERSECT",
    ]

    def __init__(self, max_query_length: int = 10000):
        self.max_query_length = max_query_length
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for efficiency."""
        self._write_pattern = re.compile(
            "|".join(self.WRITE_KEYWORDS), re.IGNORECASE
        )
        self._injection_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.INJECTION_PATTERNS
        ]

    def validate(self, sql: str) -> Tuple[bool, str]:
        """
        Validate a SQL query for security.

        Args:
            sql: The SQL query to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not sql or not sql.strip():
            return False, "Empty query"

        # Check query length
        if len(sql) > self.max_query_length:
            return False, f"Query exceeds maximum length of {self.max_query_length} characters"

        # Normalize query for checking
        normalized = sql.strip()

        # Must start with SELECT or WITH (for CTEs)
        if not re.match(r"^\s*(SELECT|WITH)\b", normalized, re.IGNORECASE):
            return False, "Query must start with SELECT or WITH"

        # Check for write operations
        if self._write_pattern.search(normalized):
            match = self._write_pattern.search(normalized)
            return False, f"Write operation detected: {match.group()}"

        # Check for injection patterns
        for pattern in self._injection_patterns:
            if pattern.search(normalized):
                return False, "Potential SQL injection pattern detected"

        # Check for multiple statements (semicolon not at end)
        # Allow semicolon only at the very end
        semicolon_count = normalized.count(";")
        if semicolon_count > 1:
            return False, "Multiple SQL statements not allowed"
        if semicolon_count == 1 and not normalized.rstrip().endswith(";"):
            return False, "Semicolon only allowed at end of query"

        return True, ""

    def sanitize_identifier(self, identifier: str) -> str:
        """
        Sanitize a SQL identifier (table or column name).

        Args:
            identifier: The identifier to sanitize

        Returns:
            Sanitized identifier safe for use in queries
        """
        # Only allow alphanumeric and underscore
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "", identifier)
        return sanitized

    def is_safe_identifier(self, identifier: str) -> bool:
        """Check if an identifier is safe to use."""
        return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", identifier))
