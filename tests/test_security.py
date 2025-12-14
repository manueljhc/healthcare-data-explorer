"""Unit tests for the security validator."""

import pytest
from utils.security import SQLValidator


class TestSQLValidator:
    """Tests for SQLValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a SQL validator instance."""
        return SQLValidator()

    # Valid SELECT queries
    def test_valid_simple_select(self, validator):
        """Test that simple SELECT is valid."""
        is_valid, error = validator.validate("SELECT * FROM users")
        assert is_valid is True
        assert error == ""

    def test_valid_select_with_where(self, validator):
        """Test SELECT with WHERE clause."""
        is_valid, _ = validator.validate(
            "SELECT name FROM users WHERE id = 1"
        )
        assert is_valid is True

    def test_valid_select_with_join(self, validator):
        """Test SELECT with JOIN."""
        is_valid, _ = validator.validate("""
            SELECT u.name, o.total
            FROM users u
            JOIN orders o ON u.id = o.user_id
        """)
        assert is_valid is True

    def test_valid_select_with_aggregation(self, validator):
        """Test SELECT with aggregation functions."""
        is_valid, _ = validator.validate(
            "SELECT country, SUM(deaths) FROM data GROUP BY country"
        )
        assert is_valid is True

    def test_valid_select_with_subquery(self, validator):
        """Test SELECT with subquery."""
        is_valid, _ = validator.validate("""
            SELECT * FROM users
            WHERE id IN (SELECT user_id FROM orders WHERE total > 100)
        """)
        assert is_valid is True

    def test_valid_cte_query(self, validator):
        """Test WITH (CTE) query."""
        is_valid, _ = validator.validate("""
            WITH active_users AS (
                SELECT * FROM users WHERE active = 1
            )
            SELECT * FROM active_users
        """)
        assert is_valid is True

    def test_valid_union_query(self, validator):
        """Test UNION query."""
        is_valid, _ = validator.validate("""
            SELECT name FROM users
            UNION
            SELECT name FROM admins
        """)
        assert is_valid is True

    # Invalid queries - write operations
    def test_invalid_insert(self, validator):
        """Test that INSERT is rejected."""
        is_valid, error = validator.validate(
            "INSERT INTO users (name) VALUES ('test')"
        )
        assert is_valid is False
        assert "INSERT" in error.upper() or "must start with SELECT" in error

    def test_invalid_update(self, validator):
        """Test that UPDATE is rejected."""
        is_valid, error = validator.validate(
            "UPDATE users SET name = 'test' WHERE id = 1"
        )
        assert is_valid is False

    def test_invalid_delete(self, validator):
        """Test that DELETE is rejected."""
        is_valid, error = validator.validate("DELETE FROM users WHERE id = 1")
        assert is_valid is False

    def test_invalid_drop(self, validator):
        """Test that DROP is rejected."""
        is_valid, error = validator.validate("DROP TABLE users")
        assert is_valid is False

    def test_invalid_truncate(self, validator):
        """Test that TRUNCATE is rejected."""
        is_valid, error = validator.validate("TRUNCATE TABLE users")
        assert is_valid is False

    def test_invalid_alter(self, validator):
        """Test that ALTER is rejected."""
        is_valid, error = validator.validate(
            "ALTER TABLE users ADD COLUMN email TEXT"
        )
        assert is_valid is False

    def test_invalid_create(self, validator):
        """Test that CREATE is rejected."""
        is_valid, error = validator.validate(
            "CREATE TABLE test (id INTEGER)"
        )
        assert is_valid is False

    # SQL injection patterns
    def test_injection_comment_after_semicolon(self, validator):
        """Test detection of comment injection."""
        is_valid, error = validator.validate("SELECT * FROM users; --")
        assert is_valid is False
        assert "injection" in error.lower() or "semicolon" in error.lower()

    def test_injection_or_1_equals_1(self, validator):
        """Test detection of OR 1=1 injection."""
        is_valid, error = validator.validate(
            "SELECT * FROM users WHERE name = '' OR 1=1"
        )
        assert is_valid is False

    def test_injection_union_select(self, validator):
        """Test detection of UNION SELECT injection."""
        # Malicious UNION injection (different from legitimate UNION)
        is_valid, error = validator.validate(
            "SELECT * FROM users WHERE id = 1 UNION ALL SELECT password FROM admin"
        )
        assert is_valid is False

    def test_injection_multiple_statements(self, validator):
        """Test rejection of multiple statements."""
        is_valid, error = validator.validate(
            "SELECT * FROM users; SELECT * FROM passwords"
        )
        assert is_valid is False
        assert "multiple" in error.lower() or "semicolon" in error.lower()

    # Edge cases
    def test_empty_query(self, validator):
        """Test handling of empty query."""
        is_valid, error = validator.validate("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_whitespace_only_query(self, validator):
        """Test handling of whitespace-only query."""
        is_valid, error = validator.validate("   \n\t  ")
        assert is_valid is False

    def test_query_too_long(self, validator):
        """Test rejection of overly long queries."""
        long_query = "SELECT " + "a, " * 5000 + "b FROM table"
        is_valid, error = validator.validate(long_query)
        assert is_valid is False
        assert "length" in error.lower()

    def test_semicolon_at_end_allowed(self, validator):
        """Test that trailing semicolon is allowed."""
        is_valid, _ = validator.validate("SELECT * FROM users;")
        assert is_valid is True

    # Identifier sanitization
    def test_sanitize_identifier_basic(self, validator):
        """Test basic identifier sanitization."""
        result = validator.sanitize_identifier("user_name")
        assert result == "user_name"

    def test_sanitize_identifier_removes_special_chars(self, validator):
        """Test that special characters are removed."""
        result = validator.sanitize_identifier("user; DROP TABLE--")
        assert result == "userDROPTABLE"
        assert ";" not in result
        assert "-" not in result

    def test_is_safe_identifier_valid(self, validator):
        """Test safe identifier validation."""
        assert validator.is_safe_identifier("user_name") is True
        assert validator.is_safe_identifier("Table1") is True
        assert validator.is_safe_identifier("_private") is True

    def test_is_safe_identifier_invalid(self, validator):
        """Test unsafe identifier detection."""
        assert validator.is_safe_identifier("123start") is False
        assert validator.is_safe_identifier("user-name") is False
        assert validator.is_safe_identifier("user name") is False
        assert validator.is_safe_identifier("") is False


class TestSQLValidatorCaseInsensitivity:
    """Test that validation is case-insensitive."""

    @pytest.fixture
    def validator(self):
        return SQLValidator()

    def test_select_case_insensitive(self, validator):
        """Test that SELECT works in any case."""
        assert validator.validate("select * from users")[0] is True
        assert validator.validate("SELECT * FROM users")[0] is True
        assert validator.validate("Select * From Users")[0] is True

    def test_insert_case_insensitive(self, validator):
        """Test that INSERT is blocked in any case."""
        assert validator.validate("insert into users values (1)")[0] is False
        assert validator.validate("INSERT INTO users VALUES (1)")[0] is False
        assert validator.validate("Insert Into Users Values (1)")[0] is False

    def test_delete_case_insensitive(self, validator):
        """Test that DELETE is blocked in any case."""
        assert validator.validate("delete from users")[0] is False
        assert validator.validate("DELETE FROM users")[0] is False
        assert validator.validate("Delete From Users")[0] is False
