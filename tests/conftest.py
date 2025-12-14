"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path
import tempfile
import sqlite3

from database.connection import DatabaseConnection
from database.data_dictionary import DataDictionary
from tools.discovery import DiscoveryTool
from tools.sql_executor import SQLExecutorTool
from tools.visualization import VisualizationTool
from utils.security import SQLValidator


@pytest.fixture
def temp_db_path():
    """Create a temporary database file path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield Path(f.name)


@pytest.fixture
def sample_db(temp_db_path):
    """Create a sample database with test data."""
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()

    # Create test tables
    cursor.execute("""
        CREATE TABLE countries (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            region TEXT NOT NULL,
            population INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE health_metrics (
            id INTEGER PRIMARY KEY,
            country_id INTEGER,
            metric_name TEXT NOT NULL,
            value REAL NOT NULL,
            year INTEGER NOT NULL,
            FOREIGN KEY (country_id) REFERENCES countries(id)
        )
    """)

    # Insert test data
    countries = [
        (1, "Ghana", "West Africa", 31000000),
        (2, "Kenya", "East Africa", 54000000),
        (3, "Nigeria", "West Africa", 206000000),
    ]
    cursor.executemany("INSERT INTO countries VALUES (?, ?, ?, ?)", countries)

    metrics = [
        (1, 1, "life_expectancy", 64.1, 2023),
        (2, 1, "infant_mortality", 32.5, 2023),
        (3, 2, "life_expectancy", 66.7, 2023),
        (4, 2, "infant_mortality", 28.9, 2023),
        (5, 3, "life_expectancy", 55.2, 2023),
        (6, 3, "infant_mortality", 72.2, 2023),
        (7, 1, "life_expectancy", 63.5, 2022),
        (8, 2, "life_expectancy", 65.9, 2022),
    ]
    cursor.executemany("INSERT INTO health_metrics VALUES (?, ?, ?, ?, ?)", metrics)

    conn.commit()
    conn.close()

    yield temp_db_path

    # Cleanup
    temp_db_path.unlink(missing_ok=True)


@pytest.fixture
def db_connection(sample_db):
    """Create a database connection to the sample database."""
    return DatabaseConnection(db_path=sample_db)


@pytest.fixture
def discovery_tool(db_connection):
    """Create a discovery tool instance."""
    return DiscoveryTool(db_connection)


@pytest.fixture
def sql_validator():
    """Create a SQL validator instance."""
    return SQLValidator()


@pytest.fixture
def sql_executor(db_connection, sql_validator):
    """Create a SQL executor tool instance."""
    return SQLExecutorTool(db_connection, sql_validator)


@pytest.fixture
def visualization_tool():
    """Create a visualization tool instance."""
    return VisualizationTool()


@pytest.fixture
def sample_query_results():
    """Sample query results for visualization tests."""
    return [
        {"country": "Ghana", "deaths": 5000, "year": 2023},
        {"country": "Kenya", "deaths": 8000, "year": 2023},
        {"country": "Nigeria", "deaths": 15000, "year": 2023},
        {"country": "South Africa", "deaths": 12000, "year": 2023},
        {"country": "Ethiopia", "deaths": 9000, "year": 2023},
    ]


@pytest.fixture
def sample_time_series_data():
    """Sample time series data for visualization tests."""
    # Use string years so they're detected as categorical (for line chart suggestion)
    return [
        {"year": "2019", "deaths": 10000, "country": "Ghana"},
        {"year": "2020", "deaths": 11000, "country": "Ghana"},
        {"year": "2021", "deaths": 10500, "country": "Ghana"},
        {"year": "2022", "deaths": 9800, "country": "Ghana"},
        {"year": "2023", "deaths": 9500, "country": "Ghana"},
    ]
