"""Streamlit frontend for the Healthcare Data Explorer."""

import os

import pandas as pd
import plotly.io as pio
import streamlit as st

from agent.orchestrator import HealthcareDataAgent
from database.data_dictionary import get_data_dictionary, DataDictionary
from tools.visualization import VisualizationTool


# Page configuration
st.set_page_config(
    page_title="AHDC Data Explorer",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS - narrower sidebar and improved styling
st.markdown("""
<style>
    /* Narrower sidebar */
    [data-testid="stSidebar"] {
        min-width: 250px;
        max-width: 280px;
    }
    [data-testid="stSidebar"] > div:first-child {
        width: 250px;
    }

    .stApp {
        max-width: 1400px;
        margin: 0 auto;
    }
    .sql-box {
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 1rem;
        border-radius: 0.5rem;
        font-family: 'Monaco', 'Menlo', monospace;
        font-size: 0.85rem;
        overflow-x: auto;
    }
    .insight-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        text-align: center;
    }
    .table-card {
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: #fafafa;
    }
    /* Better markdown rendering */
    .stMarkdown h2 {
        margin-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "agent" not in st.session_state:
        st.session_state.agent = None
    if "data_dictionary" not in st.session_state:
        st.session_state.data_dictionary = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "all_query_results" not in st.session_state:
        st.session_state.all_query_results = []  # Store ALL query results
    if "visualizations" not in st.session_state:
        st.session_state.visualizations = []
    if "show_data_dictionary" not in st.session_state:
        st.session_state.show_data_dictionary = False
    if "show_db_overview" not in st.session_state:
        st.session_state.show_db_overview = False
    if "pending_query" not in st.session_state:
        st.session_state.pending_query = None


def get_data_dict() -> DataDictionary:
    """Get or create the data dictionary (generated ONCE)."""
    if st.session_state.data_dictionary is None:
        st.session_state.data_dictionary = get_data_dictionary()
    return st.session_state.data_dictionary


def get_agent() -> HealthcareDataAgent:
    """Get or create the agent instance."""
    if st.session_state.agent is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            st.error("Please set the ANTHROPIC_API_KEY environment variable")
            st.stop()
        data_dict = get_data_dict()
        st.session_state.agent = HealthcareDataAgent(
            api_key=api_key,
            data_dictionary=data_dict
        )
    return st.session_state.agent


def render_data_dictionary_dialog():
    """Render the data dictionary in a dialog/modal."""
    data_dict = get_data_dict()

    st.markdown("## 📚 Data Dictionary")
    st.markdown(f"*{data_dict.database_description}*")
    st.markdown("---")

    # Summary metrics
    total_rows = sum(t.row_count for t in data_dict.tables)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tables", len(data_dict.tables))
    with col2:
        st.metric("Total Rows", f"{total_rows:,}")
    with col3:
        st.metric("Version", data_dict.version)

    st.markdown("---")

    # Table tabs
    table_names = [t.name for t in data_dict.tables]
    tabs = st.tabs(table_names)

    for tab, table in zip(tabs, data_dict.tables):
        with tab:
            st.markdown(f"**{table.description}**")
            st.markdown(f"📊 **{table.row_count:,}** rows")

            col_data = []
            for col in table.columns:
                samples = ", ".join(str(v) for v in col.sample_values[:3])
                if len(col.sample_values) > 3:
                    samples += "..."
                col_data.append({
                    "Column": col.name + (" 🔑" if col.primary_key else ""),
                    "Type": col.data_type,
                    "Description": col.description,
                    "Distinct": col.distinct_count or "-",
                    "Sample Values": samples,
                })

            df = pd.DataFrame(col_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

    # Download options
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📥 Download as JSON",
            data_dict.to_json(),
            "data_dictionary.json",
            "application/json",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "📥 Download as Markdown",
            data_dict.to_markdown(),
            "data_dictionary.md",
            "text/markdown",
            use_container_width=True,
        )


def render_db_overview_popup():
    """Render database overview as a popup in the sidebar."""
    data_dict = get_data_dict()

    st.markdown("#### Database Tables")
    for table in data_dict.tables:
        with st.expander(f"📋 {table.name}", expanded=False):
            st.caption(f"{table.row_count:,} rows")
            st.markdown(f"*{table.description[:100]}...*" if len(table.description) > 100 else f"*{table.description}*")
            cols = [col.name for col in table.columns]
            st.code(", ".join(cols), language=None)

    # Export buttons
    st.markdown("---")
    st.download_button(
        "📥 Export Schema (JSON)",
        data_dict.to_json(),
        "schema.json",
        "application/json",
        use_container_width=True,
        key="sidebar_export_json"
    )


def render_sidebar():
    """Render the sidebar with controls."""
    data_dict = get_data_dict()

    with st.sidebar:
        st.title("🏥 AHDC Explorer")

        # Database overview toggle button
        total_rows = sum(t.row_count for t in data_dict.tables)
        st.caption(f"{len(data_dict.tables)} tables • {total_rows:,} rows")

        if st.button("📊 Database Overview", use_container_width=True, type="secondary"):
            st.session_state.show_db_overview = not st.session_state.show_db_overview

        # Collapsible database overview
        if st.session_state.show_db_overview:
            with st.container():
                render_db_overview_popup()

        st.markdown("---")

        # Controls
        if st.button("🔄 New Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.all_query_results = []
            st.session_state.visualizations = []
            st.session_state.pending_query = None
            if st.session_state.agent:
                st.session_state.agent.reset_conversation()
            st.rerun()

        # Query history
        if st.session_state.agent:
            history = st.session_state.agent.get_query_history()
            if history:
                with st.expander(f"📜 Query History ({len(history)})"):
                    for i, q in enumerate(reversed(history[-5:])):
                        st.code(q["query"][:100] + "..." if len(q["query"]) > 100 else q["query"], language="sql")
                        st.caption(f"{q['row_count']} rows • {q['execution_time']:.2f}s")

        st.markdown("---")
        st.caption("Powered by Claude & AHDC")


def format_markdown_response(text: str) -> str:
    """Fix common markdown formatting issues in responses."""
    import re

    # Ensure exactly one blank line before markdown headings
    # Matches any number of newlines (including zero) before a heading and normalizes to two
    text = re.sub(r'(?<=.)(\n*)(#{1,6}\s)', r'\n\n\2', text)

    return text


def render_chat_message(message: dict):
    """Render a single chat message."""
    role = message["role"]
    content = message["content"]

    if role == "user":
        with st.chat_message("user"):
            st.write(content)
    else:
        with st.chat_message("assistant"):
            if isinstance(content, str):
                # Apply markdown formatting fixes
                formatted_content = format_markdown_response(content)
                st.markdown(formatted_content)
            elif isinstance(content, dict):
                if "text" in content:
                    formatted_text = format_markdown_response(content["text"])
                    st.markdown(formatted_text)
                if "sql_queries" in content:
                    for i, sql in enumerate(content["sql_queries"]):
                        st.markdown(f"**SQL Query {i+1}:**")
                        st.code(sql, language="sql")
                if "visualization" in content:
                    fig = pio.from_json(content["visualization"])
                    st.plotly_chart(fig, use_container_width=True)
                if "insights" in content:
                    st.markdown("**Key Insights:**")
                    for insight in content["insights"]:
                        st.markdown(f"• {insight['finding']}")


def render_query_results(results_list: list):
    """Render all query results with data tables and export options."""
    if not results_list:
        return

    for idx, results in enumerate(results_list):
        if not results or not results.get("success"):
            continue

        st.subheader(f"📊 Query Results {idx + 1}" if len(results_list) > 1 else "📊 Query Results")

        # Metrics row
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rows", f"{results['row_count']:,}")
        with col2:
            st.metric("Columns", len(results.get("columns", [])))
        with col3:
            st.metric("Query Time", f"{results['execution_time_seconds']:.3f}s")

        # SQL query - always visible for each result
        with st.expander("View SQL Query", expanded=False):
            st.code(results["query"], language="sql")

        # Data table
        if results.get("data"):
            df = pd.DataFrame(results["data"])
            st.dataframe(df, use_container_width=True, height=min(400, 50 + len(df) * 35))

            # Export and visualize options
            col1, col2, col3 = st.columns(3)
            with col1:
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    f"query_results_{idx + 1}.csv",
                    "text/csv",
                    use_container_width=True,
                    key=f"csv_download_{idx}"
                )
            with col2:
                json_str = df.to_json(orient="records", indent=2)
                st.download_button(
                    "📥 Download JSON",
                    json_str,
                    f"query_results_{idx + 1}.json",
                    "application/json",
                    use_container_width=True,
                    key=f"json_download_{idx}"
                )
            with col3:
                if st.button("📊 Visualize", use_container_width=True, key=f"viz_btn_{idx}"):
                    create_visualization_for_results(results["data"], idx)

        st.markdown("---")


def create_visualization_for_results(data: list, result_idx: int):
    """Create visualizations for query results."""
    if not data:
        st.warning("No data to visualize")
        return

    viz_tool = VisualizationTool()

    # Get chart suggestions (up to 5)
    suggestions = viz_tool.suggest_charts(data)

    if not suggestions:
        st.warning("No suitable visualizations found for this data")
        return

    # Create all suggested charts
    created_count = 0
    for suggestion in suggestions:
        chart_result = viz_tool.create_chart(
            data,
            chart_type=suggestion["chart_type"],
            x=suggestion.get("x"),
            y=suggestion.get("y"),
            color=suggestion.get("color"),
            title=suggestion.get("rationale", f"{suggestion['chart_type'].title()} Chart")
        )

        if chart_result.get("success"):
            st.session_state.visualizations.append(chart_result)
            created_count += 1

    if created_count > 0:
        st.rerun()
    else:
        st.error("Failed to create any visualizations")


def render_visualizations(visualizations: list):
    """Render Plotly visualizations."""
    if not visualizations:
        return

    st.subheader("📈 Visualizations")

    for i, viz in enumerate(visualizations):
        if viz.get("success") and viz.get("figure_json"):
            try:
                fig = pio.from_json(viz["figure_json"])
                st.plotly_chart(fig, use_container_width=True, key=f"viz_{i}")
            except Exception as e:
                st.error(f"Error rendering visualization: {e}")


def process_user_query(query: str):
    """Process a user query through the agent."""
    agent = get_agent()

    # Create placeholder for streaming response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        sql_queries = []  # Track all SQL queries

        try:
            for chunk in agent.chat(query):
                if chunk["type"] == "text":
                    full_response += chunk["content"]
                    # Apply formatting and show with cursor
                    formatted = format_markdown_response(full_response)
                    response_placeholder.markdown(formatted + "▌")

                elif chunk["type"] == "tool_use":
                    tool_name = chunk["tool_name"]
                    with st.status(f"Using {tool_name}...", expanded=False):
                        st.json(chunk["tool_input"])

                    # Track SQL queries
                    if tool_name == "execute_sql":
                        sql_queries.append(chunk["tool_input"].get("sql", ""))

                elif chunk["type"] == "tool_result":
                    result = chunk["result"]
                    tool_name = chunk["tool_name"]

                    # Store ALL query results, not just the last one
                    if tool_name == "execute_sql" and result.get("success"):
                        st.session_state.all_query_results.append(result)

                    elif tool_name == "create_chart" and result.get("success"):
                        st.session_state.visualizations.append(result)

                elif chunk["type"] == "done":
                    # Final render without cursor
                    formatted = format_markdown_response(full_response)
                    response_placeholder.markdown(formatted)

        except Exception as e:
            st.error(f"Error processing query: {e}")
            full_response = f"I encountered an error: {str(e)}"

    # Add assistant response to messages
    st.session_state.messages.append({"role": "assistant", "content": full_response})


def main():
    """Main application entry point."""
    init_session_state()
    render_sidebar()

    # Main content area - Header with Data Dictionary button
    header_col1, header_col2 = st.columns([4, 1])
    with header_col1:
        st.title("Healthcare Data Explorer")
    with header_col2:
        if st.button("📚 Data Dictionary", use_container_width=True, type="secondary"):
            st.session_state.show_data_dictionary = not st.session_state.show_data_dictionary

    st.markdown(
        "Ask questions about global health data from the Anthropic Health Data Collaborative (AHDC)."
    )

    # Data Dictionary expandable section
    if st.session_state.show_data_dictionary:
        with st.container():
            render_data_dictionary_dialog()
            st.markdown("---")

    # Example queries
    with st.expander("💡 Example Questions"):
        example_queries = [
            "What are the leading causes of death in Ghana?",
            "How has infant mortality changed over time in Sub-Saharan Africa?",
            "Which countries have the highest vaccination coverage for measles?",
            "Compare health expenditure per capita between high-income and low-income countries",
            "Show me the trend of HIV/AIDS deaths in South Africa from 2015 to 2023",
            "What interventions have been most effective at reducing malaria?",
        ]
        cols = st.columns(2)
        for i, query in enumerate(example_queries):
            with cols[i % 2]:
                if st.button(query, key=f"example_{i}", use_container_width=True):
                    st.session_state.pending_query = query
                    st.rerun()

    st.markdown("---")

    # Check for pending query (from example buttons)
    if st.session_state.pending_query:
        query = st.session_state.pending_query
        st.session_state.pending_query = None

        # Clear previous results
        st.session_state.all_query_results = []
        st.session_state.visualizations = []

        # Show user message immediately
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.write(query)

        # Process the query
        process_user_query(query)
        st.rerun()

    # Chat history
    for message in st.session_state.messages:
        render_chat_message(message)

    # Results section - show ALL query results
    if st.session_state.all_query_results:
        render_query_results(st.session_state.all_query_results)

    if st.session_state.visualizations:
        render_visualizations(st.session_state.visualizations)

    # Chat input
    if prompt := st.chat_input("Ask a question about global health data..."):
        # Clear previous results for new query
        st.session_state.all_query_results = []
        st.session_state.visualizations = []

        # Show user message immediately
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # Process the query
        process_user_query(prompt)
        st.rerun()


if __name__ == "__main__":
    main()
