"""Visualization tool for creating charts and deriving insights."""

import json
from typing import Any, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class VisualizationTool:
    """Tool for creating visualizations and deriving insights from data."""

    # Chart type recommendations based on data characteristics
    CHART_RECOMMENDATIONS = {
        "comparison": ["bar", "grouped_bar", "horizontal_bar"],
        "trend": ["line", "area"],
        "distribution": ["histogram", "box", "violin"],
        "composition": ["pie", "stacked_bar", "treemap"],
        "relationship": ["scatter", "bubble"],
        "geographic": ["choropleth", "scatter_geo"],
    }

    def suggest_charts(self, data: list[dict], query_intent: str = "") -> list[dict]:
        """
        Suggest appropriate chart types based on the data structure.

        Args:
            data: Query results as list of dictionaries
            query_intent: Optional description of what the user wants to see

        Returns:
            List of chart suggestions with rationale
        """
        if not data:
            return []

        df = pd.DataFrame(data)
        suggestions = []

        # Analyze column types
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()

        num_rows = len(df)
        num_numeric = len(numeric_cols)
        num_categorical = len(categorical_cols)

        # Bar chart: categorical + numeric
        if num_categorical >= 1 and num_numeric >= 1:
            suggestions.append({
                "chart_type": "bar",
                "x": categorical_cols[0],
                "y": numeric_cols[0],
                "rationale": f"Compare {numeric_cols[0]} across different {categorical_cols[0]} values",
            })

        # Pie chart: categorical + numeric with few categories
        if num_categorical >= 1 and num_numeric >= 1:
            unique_cats = df[categorical_cols[0]].nunique()
            if unique_cats <= 10:
                suggestions.append({
                    "chart_type": "pie",
                    "values": numeric_cols[0],
                    "names": categorical_cols[0],
                    "rationale": f"Show composition/distribution of {numeric_cols[0]} by {categorical_cols[0]}",
                })

        # Line chart: if there's a year/date column
        date_cols = [c for c in categorical_cols if any(
            term in c.lower() for term in ["year", "date", "month", "time"]
        )]
        if date_cols and num_numeric >= 1:
            suggestions.append({
                "chart_type": "line",
                "x": date_cols[0],
                "y": numeric_cols[0],
                "rationale": f"Show trend of {numeric_cols[0]} over {date_cols[0]}",
            })

        # Scatter plot: two numeric columns
        if num_numeric >= 2:
            suggestions.append({
                "chart_type": "scatter",
                "x": numeric_cols[0],
                "y": numeric_cols[1],
                "rationale": f"Explore relationship between {numeric_cols[0]} and {numeric_cols[1]}",
            })

        # Grouped bar: multiple categories
        if num_categorical >= 2 and num_numeric >= 1:
            suggestions.append({
                "chart_type": "grouped_bar",
                "x": categorical_cols[0],
                "y": numeric_cols[0],
                "color": categorical_cols[1],
                "rationale": f"Compare {numeric_cols[0]} across {categorical_cols[0]}, grouped by {categorical_cols[1]}",
            })

        # Histogram: single numeric column
        if num_numeric >= 1:
            suggestions.append({
                "chart_type": "histogram",
                "x": numeric_cols[0],
                "rationale": f"Show distribution of {numeric_cols[0]} values",
            })

        return suggestions[:5]  # Return top 5 suggestions

    def create_chart(
        self,
        data: list[dict],
        chart_type: str,
        x: Optional[str] = None,
        y: Optional[str] = None,
        color: Optional[str] = None,
        title: Optional[str] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Create a Plotly chart from the data.

        Args:
            data: Query results as list of dictionaries
            chart_type: Type of chart to create
            x: Column for x-axis
            y: Column for y-axis
            color: Column for color grouping
            title: Chart title
            **kwargs: Additional chart-specific parameters

        Returns:
            Dictionary with Plotly figure JSON and metadata
        """
        if not data:
            return {"error": "No data provided"}

        df = pd.DataFrame(data)

        try:
            fig = self._create_figure(df, chart_type, x, y, color, title, **kwargs)

            # Apply consistent styling
            fig.update_layout(
                template="plotly_white",
                title_font_size=16,
                legend_title_font_size=12,
                margin=dict(l=50, r=50, t=60, b=50),
            )

            return {
                "success": True,
                "chart_type": chart_type,
                "figure_json": fig.to_json(),
                "figure_html": fig.to_html(include_plotlyjs="cdn", full_html=False),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "chart_type": chart_type,
            }

    def _create_figure(
        self,
        df: pd.DataFrame,
        chart_type: str,
        x: Optional[str],
        y: Optional[str],
        color: Optional[str],
        title: Optional[str],
        **kwargs,
    ) -> go.Figure:
        """Create the appropriate Plotly figure."""

        chart_creators = {
            "bar": lambda: px.bar(df, x=x, y=y, color=color, title=title, **kwargs),
            "horizontal_bar": lambda: px.bar(df, x=y, y=x, color=color, title=title, orientation="h", **kwargs),
            "grouped_bar": lambda: px.bar(df, x=x, y=y, color=color, title=title, barmode="group", **kwargs),
            "stacked_bar": lambda: px.bar(df, x=x, y=y, color=color, title=title, barmode="stack", **kwargs),
            "line": lambda: px.line(df, x=x, y=y, color=color, title=title, markers=True, **kwargs),
            "area": lambda: px.area(df, x=x, y=y, color=color, title=title, **kwargs),
            "scatter": lambda: px.scatter(df, x=x, y=y, color=color, title=title, **kwargs),
            "bubble": lambda: px.scatter(df, x=x, y=y, color=color, size=kwargs.get("size"), title=title),
            "pie": lambda: px.pie(df, values=y or kwargs.get("values"), names=x or kwargs.get("names"), title=title),
            "histogram": lambda: px.histogram(df, x=x, color=color, title=title, **kwargs),
            "box": lambda: px.box(df, x=x, y=y, color=color, title=title, **kwargs),
            "violin": lambda: px.violin(df, x=x, y=y, color=color, title=title, **kwargs),
            "treemap": lambda: px.treemap(df, path=kwargs.get("path", [x]), values=y, title=title),
            "choropleth": lambda: px.choropleth(
                df,
                locations=kwargs.get("locations", x),
                locationmode=kwargs.get("locationmode", "country names"),
                color=y,
                title=title,
            ),
            "scatter_geo": lambda: px.scatter_geo(
                df,
                locations=kwargs.get("locations", x),
                locationmode=kwargs.get("locationmode", "country names"),
                size=y,
                color=color,
                title=title,
            ),
        }

        if chart_type not in chart_creators:
            raise ValueError(f"Unsupported chart type: {chart_type}")

        return chart_creators[chart_type]()

    def derive_insights(self, data: list[dict], context: str = "") -> dict[str, Any]:
        """
        Derive statistical insights from the data.

        Args:
            data: Query results as list of dictionaries
            context: Context about what the data represents

        Returns:
            Dictionary with derived insights
        """
        if not data:
            return {"insights": [], "summary": "No data to analyze"}

        df = pd.DataFrame(data)
        insights = []

        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()

        # Basic statistics for numeric columns
        for col in numeric_cols:
            stats = df[col].describe()
            insights.append({
                "type": "statistic",
                "column": col,
                "finding": f"{col}: mean={stats['mean']:.2f}, median={df[col].median():.2f}, "
                          f"range=[{stats['min']:.2f}, {stats['max']:.2f}]",
            })

            # Check for outliers
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            outliers = df[(df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)]
            if len(outliers) > 0:
                insights.append({
                    "type": "outlier",
                    "column": col,
                    "finding": f"{len(outliers)} potential outliers detected in {col}",
                })

        # Top/bottom values for categorical + numeric combinations
        if categorical_cols and numeric_cols:
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]

            # Top values
            top_5 = df.nlargest(5, num_col)[[cat_col, num_col]]
            if not top_5.empty:
                top_items = [f"{row[cat_col]} ({row[num_col]:,.0f})" for _, row in top_5.iterrows()]
                insights.append({
                    "type": "ranking",
                    "finding": f"Top 5 by {num_col}: {', '.join(top_items)}",
                })

            # Bottom values
            bottom_5 = df.nsmallest(5, num_col)[[cat_col, num_col]]
            if not bottom_5.empty:
                bottom_items = [f"{row[cat_col]} ({row[num_col]:,.0f})" for _, row in bottom_5.iterrows()]
                insights.append({
                    "type": "ranking",
                    "finding": f"Bottom 5 by {num_col}: {', '.join(bottom_items)}",
                })

        # Concentration analysis
        if numeric_cols:
            num_col = numeric_cols[0]
            total = df[num_col].sum()
            if total > 0:
                df_sorted = df.sort_values(num_col, ascending=False)
                top_20_pct = df_sorted.head(max(1, len(df) // 5))[num_col].sum()
                concentration = (top_20_pct / total) * 100
                insights.append({
                    "type": "concentration",
                    "finding": f"Top 20% of entries account for {concentration:.1f}% of total {num_col}",
                })

        # Build summary
        summary_parts = [f"Analyzed {len(df)} rows with {len(df.columns)} columns."]
        if numeric_cols:
            summary_parts.append(f"Numeric columns: {', '.join(numeric_cols)}.")
        if categorical_cols:
            summary_parts.append(f"Categorical columns: {', '.join(categorical_cols)}.")

        return {
            "insights": insights,
            "summary": " ".join(summary_parts),
            "row_count": len(df),
            "column_count": len(df.columns),
        }

    def create_dashboard(
        self, data: list[dict], charts: list[dict]
    ) -> dict[str, Any]:
        """
        Create a multi-chart dashboard.

        Args:
            data: Query results as list of dictionaries
            charts: List of chart configurations

        Returns:
            Dictionary with combined dashboard figure
        """
        if not data or not charts:
            return {"error": "Data and chart configurations required"}

        n_charts = len(charts)
        cols = min(2, n_charts)
        rows = (n_charts + cols - 1) // cols

        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=[c.get("title", f"Chart {i+1}") for i, c in enumerate(charts)],
        )

        df = pd.DataFrame(data)

        for i, chart_config in enumerate(charts):
            row = i // cols + 1
            col = i % cols + 1

            chart_type = chart_config.get("chart_type", "bar")
            x = chart_config.get("x")
            y = chart_config.get("y")

            try:
                if chart_type == "bar" and x and y:
                    fig.add_trace(
                        go.Bar(x=df[x], y=df[y], name=y),
                        row=row,
                        col=col,
                    )
                elif chart_type == "line" and x and y:
                    fig.add_trace(
                        go.Scatter(x=df[x], y=df[y], mode="lines+markers", name=y),
                        row=row,
                        col=col,
                    )
                elif chart_type == "scatter" and x and y:
                    fig.add_trace(
                        go.Scatter(x=df[x], y=df[y], mode="markers", name=f"{x} vs {y}"),
                        row=row,
                        col=col,
                    )
            except Exception as e:
                continue

        fig.update_layout(
            height=400 * rows,
            showlegend=True,
            template="plotly_white",
        )

        return {
            "success": True,
            "figure_json": fig.to_json(),
            "figure_html": fig.to_html(include_plotlyjs="cdn", full_html=False),
            "chart_count": n_charts,
        }


# Tool definitions for the Agent SDK
VISUALIZATION_TOOLS = [
    {
        "name": "suggest_charts",
        "description": "Analyze query results and suggest appropriate chart types based on the data structure. Returns a list of recommended visualizations with rationale.",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "description": "Query results as list of objects",
                    "items": {"type": "object"},
                },
                "query_intent": {
                    "type": "string",
                    "description": "Optional description of what insight the user wants",
                },
            },
            "required": ["data"],
        },
    },
    {
        "name": "create_chart",
        "description": "Create a Plotly visualization from query results. Supported chart types: bar, horizontal_bar, grouped_bar, stacked_bar, line, area, scatter, bubble, pie, histogram, box, violin, treemap, choropleth, scatter_geo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "description": "Query results as list of objects",
                    "items": {"type": "object"},
                },
                "chart_type": {
                    "type": "string",
                    "description": "Type of chart to create",
                    "enum": ["bar", "horizontal_bar", "grouped_bar", "stacked_bar", "line", "area", "scatter", "bubble", "pie", "histogram", "box", "violin", "treemap", "choropleth", "scatter_geo"],
                },
                "x": {
                    "type": "string",
                    "description": "Column name for x-axis",
                },
                "y": {
                    "type": "string",
                    "description": "Column name for y-axis",
                },
                "color": {
                    "type": "string",
                    "description": "Column name for color grouping",
                },
                "title": {
                    "type": "string",
                    "description": "Chart title",
                },
            },
            "required": ["data", "chart_type"],
        },
    },
    {
        "name": "derive_insights",
        "description": "Derive statistical insights and key findings from query results. Identifies trends, outliers, top/bottom values, and concentration patterns.",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "description": "Query results as list of objects",
                    "items": {"type": "object"},
                },
                "context": {
                    "type": "string",
                    "description": "Context about what the data represents",
                },
            },
            "required": ["data"],
        },
    },
]
