"""Unit tests for the visualization tool."""

import pytest
import json


class TestVisualizationTool:
    """Tests for VisualizationTool class."""

    def test_suggest_charts_bar(self, visualization_tool, sample_query_results):
        """Test that bar chart is suggested for categorical + numeric data."""
        suggestions = visualization_tool.suggest_charts(sample_query_results)

        assert len(suggestions) > 0
        chart_types = [s["chart_type"] for s in suggestions]
        assert "bar" in chart_types

    def test_suggest_charts_pie(self, visualization_tool, sample_query_results):
        """Test that pie chart is suggested for composition data."""
        suggestions = visualization_tool.suggest_charts(sample_query_results)

        chart_types = [s["chart_type"] for s in suggestions]
        assert "pie" in chart_types

    def test_suggest_charts_line(self, visualization_tool, sample_time_series_data):
        """Test that line chart is suggested for time series data."""
        suggestions = visualization_tool.suggest_charts(sample_time_series_data)

        chart_types = [s["chart_type"] for s in suggestions]
        assert "line" in chart_types

    def test_suggest_charts_includes_rationale(self, visualization_tool, sample_query_results):
        """Test that suggestions include rationale."""
        suggestions = visualization_tool.suggest_charts(sample_query_results)

        for suggestion in suggestions:
            assert "rationale" in suggestion
            assert len(suggestion["rationale"]) > 0

    def test_suggest_charts_empty_data(self, visualization_tool):
        """Test handling of empty data."""
        suggestions = visualization_tool.suggest_charts([])

        assert suggestions == []

    def test_create_bar_chart(self, visualization_tool, sample_query_results):
        """Test creating a bar chart."""
        result = visualization_tool.create_chart(
            sample_query_results,
            chart_type="bar",
            x="country",
            y="deaths",
            title="Deaths by Country"
        )

        assert result["success"] is True
        assert result["chart_type"] == "bar"
        assert "figure_json" in result
        assert "figure_html" in result

    def test_create_line_chart(self, visualization_tool, sample_time_series_data):
        """Test creating a line chart."""
        result = visualization_tool.create_chart(
            sample_time_series_data,
            chart_type="line",
            x="year",
            y="deaths",
            title="Deaths Over Time"
        )

        assert result["success"] is True
        assert result["chart_type"] == "line"

    def test_create_pie_chart(self, visualization_tool, sample_query_results):
        """Test creating a pie chart."""
        result = visualization_tool.create_chart(
            sample_query_results,
            chart_type="pie",
            x="country",
            y="deaths",
            title="Death Distribution"
        )

        assert result["success"] is True
        assert result["chart_type"] == "pie"

    def test_create_scatter_chart(self, visualization_tool):
        """Test creating a scatter chart."""
        data = [
            {"x_val": 10, "y_val": 20},
            {"x_val": 15, "y_val": 25},
            {"x_val": 20, "y_val": 30},
        ]

        result = visualization_tool.create_chart(
            data,
            chart_type="scatter",
            x="x_val",
            y="y_val",
            title="Scatter Plot"
        )

        assert result["success"] is True
        assert result["chart_type"] == "scatter"

    def test_create_horizontal_bar_chart(self, visualization_tool, sample_query_results):
        """Test creating a horizontal bar chart."""
        result = visualization_tool.create_chart(
            sample_query_results,
            chart_type="horizontal_bar",
            x="country",
            y="deaths",
            title="Horizontal Bar"
        )

        assert result["success"] is True

    def test_create_chart_with_color(self, visualization_tool):
        """Test creating chart with color grouping."""
        data = [
            {"country": "Ghana", "deaths": 100, "year": "2022"},
            {"country": "Ghana", "deaths": 120, "year": "2023"},
            {"country": "Kenya", "deaths": 150, "year": "2022"},
            {"country": "Kenya", "deaths": 140, "year": "2023"},
        ]

        result = visualization_tool.create_chart(
            data,
            chart_type="bar",
            x="country",
            y="deaths",
            color="year",
            title="Deaths by Country and Year"
        )

        assert result["success"] is True

    def test_create_chart_empty_data(self, visualization_tool):
        """Test handling of empty data."""
        result = visualization_tool.create_chart(
            [],
            chart_type="bar",
            x="country",
            y="deaths"
        )

        assert "error" in result

    def test_create_chart_invalid_type(self, visualization_tool, sample_query_results):
        """Test handling of invalid chart type."""
        result = visualization_tool.create_chart(
            sample_query_results,
            chart_type="invalid_chart_type",
            x="country",
            y="deaths"
        )

        assert result["success"] is False
        assert "error" in result

    def test_figure_json_is_valid(self, visualization_tool, sample_query_results):
        """Test that figure_json is valid JSON."""
        result = visualization_tool.create_chart(
            sample_query_results,
            chart_type="bar",
            x="country",
            y="deaths"
        )

        assert result["success"] is True
        # Should be valid JSON
        parsed = json.loads(result["figure_json"])
        assert "data" in parsed
        assert "layout" in parsed


class TestDeriveInsights:
    """Tests for insight derivation."""

    def test_derive_insights_basic(self, visualization_tool, sample_query_results):
        """Test basic insight derivation."""
        insights = visualization_tool.derive_insights(sample_query_results)

        assert "insights" in insights
        assert "summary" in insights
        assert len(insights["insights"]) > 0

    def test_derive_insights_includes_statistics(self, visualization_tool, sample_query_results):
        """Test that insights include statistics."""
        insights = visualization_tool.derive_insights(sample_query_results)

        # Should have statistic type insights
        stat_insights = [i for i in insights["insights"] if i["type"] == "statistic"]
        assert len(stat_insights) > 0

    def test_derive_insights_includes_ranking(self, visualization_tool, sample_query_results):
        """Test that insights include rankings."""
        insights = visualization_tool.derive_insights(sample_query_results)

        ranking_insights = [i for i in insights["insights"] if i["type"] == "ranking"]
        assert len(ranking_insights) > 0

    def test_derive_insights_empty_data(self, visualization_tool):
        """Test handling of empty data."""
        insights = visualization_tool.derive_insights([])

        assert insights["insights"] == []
        assert "No data" in insights["summary"]

    def test_derive_insights_row_count(self, visualization_tool, sample_query_results):
        """Test that row count is included."""
        insights = visualization_tool.derive_insights(sample_query_results)

        assert insights["row_count"] == len(sample_query_results)

    def test_derive_insights_with_context(self, visualization_tool, sample_query_results):
        """Test insight derivation with context."""
        insights = visualization_tool.derive_insights(
            sample_query_results,
            context="Mortality data for African countries"
        )

        assert "insights" in insights


class TestChartSuggestionLogic:
    """Tests for chart suggestion logic."""

    def test_multiple_numeric_suggests_scatter(self, visualization_tool):
        """Test that multiple numeric columns suggest scatter plot."""
        data = [
            {"metric1": 10, "metric2": 20, "metric3": 30},
            {"metric1": 15, "metric2": 25, "metric3": 35},
        ]

        suggestions = visualization_tool.suggest_charts(data)

        chart_types = [s["chart_type"] for s in suggestions]
        assert "scatter" in chart_types

    def test_histogram_suggested_for_numeric(self, visualization_tool):
        """Test that histogram is suggested for numeric data."""
        data = [
            {"value": 10},
            {"value": 15},
            {"value": 20},
            {"value": 25},
        ]

        suggestions = visualization_tool.suggest_charts(data)

        chart_types = [s["chart_type"] for s in suggestions]
        assert "histogram" in chart_types

    def test_max_suggestions_limit(self, visualization_tool, sample_query_results):
        """Test that suggestions are limited."""
        suggestions = visualization_tool.suggest_charts(sample_query_results)

        assert len(suggestions) <= 5
