"""
Data Dictionary - Single source of truth for database schema and metadata.

This module generates a comprehensive data dictionary artifact once during
initialization. The artifact is then shared across all components:
- Agent orchestrator (for system prompt context)
- SQL executor (for query validation)
- Frontend (for user reference)
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
import hashlib

from database.connection import DatabaseConnection


@dataclass
class ColumnInfo:
    """Information about a database column."""
    name: str
    data_type: str
    nullable: bool
    primary_key: bool
    description: str = ""
    sample_values: list = field(default_factory=list)
    distinct_count: Optional[int] = None
    null_count: Optional[int] = None


@dataclass
class TableInfo:
    """Information about a database table."""
    name: str
    description: str
    row_count: int
    columns: list[ColumnInfo]

    @property
    def column_names(self) -> list[str]:
        return [col.name for col in self.columns]


@dataclass
class DataDictionary:
    """
    Complete data dictionary for the AHDC database.

    This is generated once and cached. It provides:
    - Schema information for all tables
    - Column metadata including types and sample values
    - Human-readable descriptions
    - Context for the LLM system prompt
    """

    database_name: str
    database_description: str
    tables: list[TableInfo]
    generated_at: str = ""
    version: str = "1.0"

    # Table descriptions for AHDC
    TABLE_DESCRIPTIONS = {
        "disease_burden": "Global Burden of Disease data tracking deaths and Disability-Adjusted Life Years (DALYs) by cause, country, age group, sex, and year. Primary table for mortality analysis.",
        "intervention_outcomes": "Health intervention effectiveness studies measuring baseline rates, post-intervention rates, and reduction percentages for various public health programs.",
        "health_system_capacity": "Healthcare infrastructure metrics including physicians, nurses, hospital beds per capita, health expenditure, and Universal Health Coverage index.",
        "immunization_coverage": "Vaccination coverage percentages by country, vaccine type, and year. Includes doses administered and target population groups.",
        "maternal_child_health": "Maternal and child health indicators including mortality rates (maternal, infant, under-5, neonatal), skilled birth attendance, and antenatal care coverage.",
        "infectious_disease_surveillance": "Disease outbreak and surveillance data tracking confirmed/suspected cases, deaths, case fatality rates, and outbreak status by country and time period.",
    }

    # Column descriptions
    COLUMN_DESCRIPTIONS = {
        # Common columns
        "country": "Country name",
        "country_code": "ISO 3-letter country code",
        "region": "Geographic region (e.g., Sub-Saharan Africa, South Asia)",
        "income_group": "World Bank income classification (Low, Lower middle, Upper middle, High)",
        "year": "Calendar year of the data",

        # disease_burden
        "cause_of_death": "Specific cause of death (e.g., Malaria, HIV/AIDS, Stroke)",
        "deaths": "Number of deaths",
        "dalys_thousands": "Disability-Adjusted Life Years in thousands",
        "age_group": "Age range (0-4, 5-14, 15-29, 30-44, 45-59, 60-74, 75+)",
        "sex": "Biological sex (Male, Female)",
        "data_source": "Data source organization",

        # intervention_outcomes
        "intervention_type": "Type of health intervention (e.g., Bed net distribution, Vaccination)",
        "target_condition": "Health condition targeted by the intervention",
        "baseline_rate_per_100k": "Disease rate per 100,000 before intervention",
        "post_intervention_rate_per_100k": "Disease rate per 100,000 after intervention",
        "reduction_percent": "Percentage reduction achieved",
        "study_year": "Year the study was conducted",
        "sample_size": "Number of participants in the study",
        "confidence_interval_lower": "Lower bound of 95% confidence interval",
        "confidence_interval_upper": "Upper bound of 95% confidence interval",
        "study_quality": "Quality rating of the study (High, Moderate, Low)",

        # health_system_capacity
        "physicians_per_10k": "Number of physicians per 10,000 population",
        "nurses_per_10k": "Number of nurses per 10,000 population",
        "hospital_beds_per_10k": "Hospital beds per 10,000 population",
        "health_expenditure_pct_gdp": "Health expenditure as percentage of GDP",
        "health_expenditure_per_capita_usd": "Health expenditure per person in USD",
        "out_of_pocket_pct": "Percentage of health costs paid out-of-pocket",
        "universal_health_coverage_index": "UHC service coverage index (0-100)",

        # immunization_coverage
        "vaccine": "Vaccine type (e.g., BCG, DTP3, MCV1, Polio3)",
        "coverage_pct": "Percentage of target population vaccinated",
        "target_group": "Population group targeted for vaccination",
        "doses_administered_millions": "Total doses administered in millions",

        # maternal_child_health
        "maternal_mortality_ratio": "Maternal deaths per 100,000 live births",
        "infant_mortality_rate": "Infant deaths per 1,000 live births",
        "under5_mortality_rate": "Under-5 deaths per 1,000 live births",
        "neonatal_mortality_rate": "Neonatal deaths per 1,000 live births",
        "stillbirth_rate": "Stillbirths per 1,000 total births",
        "skilled_birth_attendance_pct": "Percentage of births attended by skilled personnel",
        "antenatal_care_4visits_pct": "Percentage receiving 4+ antenatal visits",
        "low_birthweight_pct": "Percentage of newborns with low birth weight",

        # infectious_disease_surveillance
        "disease": "Infectious disease name",
        "confirmed_cases": "Number of laboratory-confirmed cases",
        "suspected_cases": "Number of suspected/probable cases",
        "case_fatality_rate": "Proportion of cases resulting in death",
        "incidence_per_100k": "New cases per 100,000 population",
        "outbreak_status": "Current status (Sporadic, Endemic, Outbreak)",
        "month": "Month of the year (1-12)",
    }

    @classmethod
    def generate(cls, db: Optional[DatabaseConnection] = None) -> "DataDictionary":
        """
        Generate the data dictionary from the database.

        Args:
            db: Database connection (creates new one if not provided)

        Returns:
            Complete DataDictionary instance
        """
        import datetime

        if db is None:
            db = DatabaseConnection()

        tables = []
        table_names = db.get_table_names()

        for table_name in table_names:
            # Skip SQLite internal tables
            if table_name.startswith("sqlite_"):
                continue

            # Get schema info
            schema = db.get_table_schema(table_name)
            row_count = db.get_row_count(table_name)

            # Build column info
            columns = []
            for col in schema:
                col_name = col["name"]

                # Get sample values for categorical columns
                sample_values = []
                distinct_count = None
                try:
                    query = f"SELECT DISTINCT {col_name} FROM {table_name} WHERE {col_name} IS NOT NULL LIMIT 10"
                    results = db.execute_query(query)
                    sample_values = [r[col_name] for r in results]

                    # Get distinct count
                    count_query = f"SELECT COUNT(DISTINCT {col_name}) as cnt FROM {table_name}"
                    count_result = db.execute_query(count_query)
                    distinct_count = count_result[0]["cnt"] if count_result else None
                except Exception:
                    pass

                column_info = ColumnInfo(
                    name=col_name,
                    data_type=col["type"],
                    nullable=not col["notnull"],
                    primary_key=bool(col["pk"]),
                    description=cls.COLUMN_DESCRIPTIONS.get(col_name, ""),
                    sample_values=sample_values[:5],  # Limit to 5 samples
                    distinct_count=distinct_count,
                )
                columns.append(column_info)

            table_info = TableInfo(
                name=table_name,
                description=cls.TABLE_DESCRIPTIONS.get(table_name, ""),
                row_count=row_count,
                columns=columns,
            )
            tables.append(table_info)

        return cls(
            database_name="AHDC (Anthropic Health Data Collaborative)",
            database_description=(
                "Global health database maintained by the Anthropic Health Data Collaborative. "
                "Contains data on disease burden, intervention effectiveness, health systems, "
                "immunization, maternal/child health, and infectious disease surveillance "
                "across 60+ countries from 2015-2023."
            ),
            tables=tables,
            generated_at=datetime.datetime.now().isoformat(),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "database_name": self.database_name,
            "database_description": self.database_description,
            "tables": [
                {
                    "name": t.name,
                    "description": t.description,
                    "row_count": t.row_count,
                    "columns": [asdict(c) for c in t.columns],
                }
                for t in self.tables
            ],
            "generated_at": self.generated_at,
            "version": self.version,
        }

    def to_json(self, indent: int = 2) -> str:
        """Export as JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def save(self, path: Path):
        """Save data dictionary to file."""
        path.write_text(self.to_json())

    @classmethod
    def load(cls, path: Path) -> "DataDictionary":
        """Load data dictionary from file."""
        data = json.loads(path.read_text())
        tables = []
        for t in data["tables"]:
            columns = [ColumnInfo(**c) for c in t["columns"]]
            tables.append(TableInfo(
                name=t["name"],
                description=t["description"],
                row_count=t["row_count"],
                columns=columns,
            ))
        return cls(
            database_name=data["database_name"],
            database_description=data["database_description"],
            tables=tables,
            generated_at=data.get("generated_at", ""),
            version=data.get("version", "1.0"),
        )

    def get_table(self, name: str) -> Optional[TableInfo]:
        """Get a specific table by name."""
        for table in self.tables:
            if table.name == name:
                return table
        return None

    def to_llm_context(self) -> str:
        """
        Generate a formatted string for LLM system prompt context.

        This provides the LLM with complete schema information to
        write accurate SQL queries without needing to discover the schema.
        """
        lines = [
            f"# {self.database_name}",
            "",
            self.database_description,
            "",
            "## Available Tables",
            "",
        ]

        for table in self.tables:
            lines.append(f"### {table.name}")
            lines.append(f"**Description:** {table.description}")
            lines.append(f"**Rows:** {table.row_count:,}")
            lines.append("")
            lines.append("| Column | Type | Description | Sample Values |")
            lines.append("|--------|------|-------------|---------------|")

            for col in table.columns:
                samples = ", ".join(str(v) for v in col.sample_values[:3])
                if len(col.sample_values) > 3:
                    samples += "..."
                pk = " (PK)" if col.primary_key else ""
                lines.append(f"| {col.name}{pk} | {col.data_type} | {col.description} | {samples} |")

            lines.append("")

        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Generate full markdown documentation."""
        lines = [
            f"# {self.database_name} - Data Dictionary",
            "",
            f"*Generated: {self.generated_at}*",
            "",
            "## Overview",
            "",
            self.database_description,
            "",
            f"**Total Tables:** {len(self.tables)}",
            f"**Total Rows:** {sum(t.row_count for t in self.tables):,}",
            "",
            "---",
            "",
        ]

        for table in self.tables:
            lines.append(f"## {table.name}")
            lines.append("")
            lines.append(f"> {table.description}")
            lines.append("")
            lines.append(f"**Row Count:** {table.row_count:,}")
            lines.append("")
            lines.append("### Columns")
            lines.append("")
            lines.append("| Column | Type | Nullable | Description |")
            lines.append("|--------|------|----------|-------------|")

            for col in table.columns:
                nullable = "Yes" if col.nullable else "No"
                pk = " **(PK)**" if col.primary_key else ""
                lines.append(f"| {col.name}{pk} | `{col.data_type}` | {nullable} | {col.description} |")

            lines.append("")

            # Sample values section
            lines.append("### Sample Values")
            lines.append("")
            for col in table.columns:
                if col.sample_values and col.distinct_count and col.distinct_count <= 20:
                    values = ", ".join(f"`{v}`" for v in col.sample_values)
                    lines.append(f"- **{col.name}**: {values}")

            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)


# Singleton instance for application-wide use
_data_dictionary: Optional[DataDictionary] = None
_dictionary_cache_path = Path(__file__).parent / "data_dictionary_cache.json"


def get_data_dictionary(force_refresh: bool = False) -> DataDictionary:
    """
    Get the singleton data dictionary instance.

    Generates once and caches for subsequent calls.

    Args:
        force_refresh: If True, regenerate even if cached

    Returns:
        DataDictionary instance
    """
    global _data_dictionary

    if _data_dictionary is not None and not force_refresh:
        return _data_dictionary

    # Try to load from cache first
    if _dictionary_cache_path.exists() and not force_refresh:
        try:
            _data_dictionary = DataDictionary.load(_dictionary_cache_path)
            return _data_dictionary
        except Exception:
            pass  # Cache invalid, regenerate

    # Generate fresh
    _data_dictionary = DataDictionary.generate()

    # Save to cache
    try:
        _data_dictionary.save(_dictionary_cache_path)
    except Exception:
        pass  # Non-critical if cache save fails

    return _data_dictionary
