# Healthcare Data Explorer

A natural language interface for exploring global health data from the Anthropic Health Data Collaborative (AHDC). Ask questions in plain English and get SQL queries, visualizations, and insights.

## Features

- **Natural Language Queries**: Ask questions like "What are the leading causes of death in Ghana?"
- **Automatic SQL Generation**: Claude generates optimized, read-only SQL queries
- **Interactive Visualizations**: Plotly charts chosen based on your data
- **Data Insights**: Automatic statistical analysis and key findings
- **Export Options**: Download results as CSV or JSON
- **Query Validation**: Built-in security to prevent data modification

## Database

The AHDC database contains global health data across 60+ countries:

| Table | Description | Rows |
|-------|-------------|------|
| `disease_burden` | Deaths and DALYs by cause, country, age, sex | ~145K |
| `intervention_outcomes` | Health intervention effectiveness studies | ~5.7K |
| `health_system_capacity` | Healthcare infrastructure metrics | ~570 |
| `immunization_coverage` | Vaccination coverage by country/vaccine | ~5.9K |
| `maternal_child_health` | Maternal and child health indicators | ~570 |
| `infectious_disease_surveillance` | Disease outbreak data | ~58K |

## Quick Start

### 1. Set up environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API key

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your Anthropic API key
export ANTHROPIC_API_KEY=your-api-key-here
```

### 3. Initialize the database

```bash
python database/setup_sample_data.py
```

### 4. Run the application

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Example Queries

- "What are the leading causes of mortality in Ghana?"
- "Show me the trend of infant mortality in Sub-Saharan Africa over time"
- "Which countries have the highest vaccination coverage?"
- "Compare health expenditure between high and low income countries"
- "What interventions have been most effective at reducing malaria?"

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Streamlit Frontend                     │
│         (Query input, SQL preview, visualizations)       │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              Agent Orchestrator (Claude)                 │
│     Interprets queries, coordinates tools, generates     │
│              insights and visualizations                 │
└─────────────────────────────────────────────────────────┘
         │                 │                  │
         │    ┌────────────┴────────────┐     │
         │    ▼                         ▼     │
         │  ┌───────────────────────────────┐ │
         │  │      Data Dictionary          │ │
         │  │  (Cached schema + metadata)   │ │
         │  └───────────────────────────────┘ │
         │           │ generated once         │
         ▼           ▼                        ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│   Discovery   │ │ SQL Executor  │ │ Visualization │
│     Tool      │ │    Tool       │ │     Tool      │
└───────────────┘ └───────────────┘ └───────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                    ┌─────────────┐
                    │   SQLite    │
                    │  Database   │
                    └─────────────┘
```

The **Data Dictionary** is generated once on startup by the Discovery Tool, then cached and shared with the Orchestrator and SQL Executor. This avoids repeated schema queries and provides consistent metadata context to the LLM.

## Security Measures

- **Read-only SQL**: Only SELECT queries are allowed
- **Query validation**: Regex + pattern matching to block dangerous operations
- **SQL injection prevention**: Input sanitization and parameterized queries
- **Row limits**: Maximum 10,000 rows per query
- **Query timeout**: 30-second execution limit
- **User approval**: Option to review SQL before execution

## Project Structure

```
healthcare-data-explorer/
├── app.py                 # Streamlit frontend
├── agent/
│   ├── orchestrator.py    # Main agent with tool coordination
│   └── prompts.py         # System prompts
├── tools/
│   ├── discovery.py       # Database schema exploration
│   ├── sql_executor.py    # Query validation & execution
│   └── visualization.py   # Plotly charts & insights
├── database/
│   ├── connection.py      # DB connection management
│   ├── data_dictionary.py # Cached schema & metadata (generated once)
│   ├── setup_sample_data.py # Sample data generator
│   └── healthcare.db      # SQLite database
├── utils/
│   ├── security.py        # SQL validation
│   └── export.py          # Data export utilities
└── requirements.txt
```

## Development

### Running tests

```bash
python -c "
from database.connection import DatabaseConnection
from tools.discovery import DiscoveryTool

db = DatabaseConnection()
discovery = DiscoveryTool(db)
print(discovery.get_schema_summary())
"
```

### Adding new tools

1. Create tool class in `tools/`
2. Define tool schema following the existing pattern
3. Register tool in `agent/orchestrator.py`

## License

MIT
