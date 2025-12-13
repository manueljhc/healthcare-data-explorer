"""Main agent orchestrator using Anthropic API with tool use."""

import json
from typing import Any, Generator, Optional

import anthropic

from agent.prompts import build_system_prompt
from database.connection import DatabaseConnection
from database.data_dictionary import DataDictionary, get_data_dictionary
from tools.discovery import DiscoveryTool, DISCOVERY_TOOLS
from tools.sql_executor import SQLExecutorTool, SQL_EXECUTOR_TOOLS
from tools.visualization import VisualizationTool, VISUALIZATION_TOOLS
from utils.security import SQLValidator


class HealthcareDataAgent:
    """Agent for natural language exploration of healthcare data."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        db_path: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        data_dictionary: Optional[DataDictionary] = None,
    ):
        """
        Initialize the healthcare data agent.

        Args:
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided)
            db_path: Path to SQLite database
            model: Claude model to use
            data_dictionary: Pre-generated data dictionary (generates one if not provided)
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Initialize database and tools
        self.db = DatabaseConnection(db_path=db_path) if db_path else DatabaseConnection()
        self.validator = SQLValidator()
        self.discovery = DiscoveryTool(self.db)
        self.sql_executor = SQLExecutorTool(self.db, self.validator)
        self.visualization = VisualizationTool()

        # Load or use provided data dictionary (generated ONCE)
        self.data_dictionary = data_dictionary or get_data_dictionary()

        # Build system prompt with data dictionary context
        self.system_prompt = build_system_prompt(self.data_dictionary.to_llm_context())

        # Conversation history
        self.messages: list[dict] = []

        # Tools available to the agent
        # Discovery tools are still available but rarely needed since schema is in prompt
        self.tools = DISCOVERY_TOOLS + SQL_EXECUTOR_TOOLS + VISUALIZATION_TOOLS

        # Track state
        self.last_query_results: Optional[list[dict]] = None
        self.pending_sql: Optional[str] = None

    def _handle_tool_call(self, tool_name: str, tool_input: dict) -> Any:
        """Execute a tool call and return the result."""

        # Discovery tools (available but rarely needed)
        if tool_name == "get_database_overview":
            return self.discovery.get_database_overview()
        elif tool_name == "get_table_details":
            return self.discovery.get_table_details(tool_input["table_name"])
        elif tool_name == "get_column_values":
            return self.discovery.get_column_values(
                tool_input["table_name"],
                tool_input["column_name"],
                tool_input.get("limit", 100),
            )
        elif tool_name == "search_columns":
            return self.discovery.search_columns(tool_input["search_term"])

        # SQL tools
        elif tool_name == "validate_sql":
            return self.sql_executor.validate_query(tool_input["sql"])
        elif tool_name == "execute_sql":
            result = self.sql_executor.execute_query(tool_input["sql"])
            if result.get("success"):
                self.last_query_results = result.get("data", [])
            return result
        elif tool_name == "export_results":
            results = tool_input.get("results", self.last_query_results or [])
            return self.sql_executor.export_results(
                results, tool_input.get("format", "csv")
            )

        # Visualization tools
        elif tool_name == "suggest_charts":
            data = tool_input.get("data", self.last_query_results or [])
            return self.visualization.suggest_charts(
                data, tool_input.get("query_intent", "")
            )
        elif tool_name == "create_chart":
            data = tool_input.get("data", self.last_query_results or [])
            return self.visualization.create_chart(
                data,
                tool_input["chart_type"],
                x=tool_input.get("x"),
                y=tool_input.get("y"),
                color=tool_input.get("color"),
                title=tool_input.get("title"),
            )
        elif tool_name == "derive_insights":
            data = tool_input.get("data", self.last_query_results or [])
            return self.visualization.derive_insights(
                data, tool_input.get("context", "")
            )

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    def chat(self, user_message: str) -> Generator[dict, None, None]:
        """
        Process a user message and yield response chunks.

        Args:
            user_message: The user's natural language query

        Yields:
            Response chunks with type indicators (text, tool_use, tool_result, etc.)
        """
        # Add user message to history
        self.messages.append({"role": "user", "content": user_message})

        while True:
            # Call Claude with tools and data dictionary in system prompt
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                tools=self.tools,
                messages=self.messages,
            )

            # Process response content
            assistant_content = []
            tool_calls_to_process = []

            for block in response.content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                    yield {"type": "text", "content": block.text}

                elif block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })
                    yield {
                        "type": "tool_use",
                        "tool_name": block.name,
                        "tool_input": block.input,
                    }
                    tool_calls_to_process.append(block)

            # Add assistant response to history
            self.messages.append({"role": "assistant", "content": assistant_content})

            # If no tool calls, we're done
            if not tool_calls_to_process:
                break

            # Process tool calls
            tool_results = []
            for tool_call in tool_calls_to_process:
                result = self._handle_tool_call(tool_call.name, tool_call.input)

                # Yield tool result
                yield {
                    "type": "tool_result",
                    "tool_name": tool_call.name,
                    "result": result,
                }

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": json.dumps(result, default=str),
                })

            # Add tool results to history
            self.messages.append({"role": "user", "content": tool_results})

            # Check if we should stop (end_turn) or continue
            if response.stop_reason == "end_turn":
                break

        yield {"type": "done"}

    def chat_sync(self, user_message: str) -> dict:
        """
        Process a user message and return the complete response.

        Args:
            user_message: The user's natural language query

        Returns:
            Complete response with all text, tool uses, and results
        """
        response = {
            "text_parts": [],
            "tool_calls": [],
            "visualizations": [],
            "query_results": None,
            "exports": [],
        }

        for chunk in self.chat(user_message):
            if chunk["type"] == "text":
                response["text_parts"].append(chunk["content"])

            elif chunk["type"] == "tool_use":
                response["tool_calls"].append({
                    "name": chunk["tool_name"],
                    "input": chunk["tool_input"],
                })

            elif chunk["type"] == "tool_result":
                result = chunk["result"]
                tool_name = chunk["tool_name"]

                if tool_name == "execute_sql" and result.get("success"):
                    response["query_results"] = result

                elif tool_name == "create_chart" and result.get("success"):
                    response["visualizations"].append(result)

                elif tool_name == "export_results" and "data" in result:
                    response["exports"].append(result)

        response["full_text"] = "\n".join(response["text_parts"])
        return response

    def get_data_dictionary(self) -> DataDictionary:
        """Get the data dictionary artifact."""
        return self.data_dictionary

    def get_schema_context(self) -> str:
        """Get a formatted schema description for context."""
        return self.data_dictionary.to_llm_context()

    def reset_conversation(self):
        """Reset the conversation history."""
        self.messages = []
        self.last_query_results = None
        self.pending_sql = None

    def approve_sql(self, sql: str) -> dict:
        """
        Approve and execute a pending SQL query.

        Args:
            sql: The SQL query to execute

        Returns:
            Query execution result
        """
        result = self.sql_executor.execute_query(sql)
        if result.get("success"):
            self.last_query_results = result.get("data", [])
        return result

    def get_query_history(self) -> list[dict]:
        """Get the history of executed queries."""
        return self.sql_executor.get_query_history()
