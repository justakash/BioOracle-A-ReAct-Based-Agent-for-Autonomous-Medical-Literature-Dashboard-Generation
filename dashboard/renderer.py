"""
Dashboard Renderer
Reads a dashboard config produced by the agent and builds a Plotly Dash layout.
"""

import json
import os
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from loguru import logger


class DashboardRenderer:
    """
    Converts a dashboard configuration dict into a rendered Plotly Dash application.
    """

    def __init__(self):
        self.data_dir = os.getenv("DATA_DIR", "./data")
        self.export_dir = os.getenv("EXPORT_DIR", "./exports")
        os.makedirs(self.export_dir, exist_ok=True)

    def _load_config(self, config_id: str) -> dict:
        config_path = os.path.join(self.data_dir, f"dashboard_config_{config_id}.json")
        with open(config_path, "r") as f:
            return json.load(f)

    def _load_data(self, csv_path: str) -> pd.DataFrame:
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Data file not found: {csv_path}")
        return pd.read_csv(csv_path)

    def _build_figure(self, chart: dict, df: pd.DataFrame) -> go.Figure:
        """Build a Plotly figure from a chart spec and DataFrame."""
        chart_type = chart.get("chart_type", "bar")
        title = chart.get("title", "")
        x_col = chart.get("x_column")
        y_col = chart.get("y_column")
        color_col = chart.get("color_column")
        aggregation = chart.get("aggregation", "count")
        top_n = chart.get("top_n")

        try:
            # Aggregate if needed
            if aggregation == "count" and x_col and x_col in df.columns:
                agg_df = df[x_col].value_counts().reset_index()
                agg_df.columns = [x_col, "count"]
                if top_n:
                    agg_df = agg_df.head(top_n)
                plot_df = agg_df
                y_col = "count"
            elif aggregation in ("sum", "mean", "median", "max", "min") and x_col and y_col:
                agg_df = df.groupby(x_col)[y_col].agg(aggregation).reset_index()
                if top_n:
                    agg_df = agg_df.nlargest(top_n, y_col)
                plot_df = agg_df
            else:
                plot_df = df

            fig = None

            if chart_type == "bar":
                fig = px.bar(plot_df, x=x_col, y=y_col, color=color_col, title=title)
                if top_n:
                    fig.update_layout(xaxis={"categoryorder": "total descending"})

            elif chart_type == "line":
                fig = px.line(plot_df, x=x_col, y=y_col, color=color_col, title=title, markers=True)

            elif chart_type == "pie":
                fig = px.pie(plot_df, names=x_col, values=y_col, title=title)

            elif chart_type == "donut":
                fig = px.pie(plot_df, names=x_col, values=y_col, title=title, hole=0.4)

            elif chart_type == "scatter":
                fig = px.scatter(plot_df, x=x_col, y=y_col, color=color_col, title=title)

            elif chart_type == "treemap":
                path_cols = [x_col] if x_col else [plot_df.columns[0]]
                fig = px.treemap(plot_df, path=path_cols, values=y_col, title=title)

            elif chart_type == "heatmap":
                pivot = plot_df.pivot_table(index=x_col, columns=color_col, values=y_col, aggfunc="sum")
                fig = px.imshow(pivot, title=title)

            elif chart_type == "choropleth":
                fig = px.choropleth(plot_df, locations=x_col, color=y_col, title=title,
                                    locationmode="country names")

            elif chart_type == "histogram":
                fig = px.histogram(plot_df, x=x_col, color=color_col, title=title)

            elif chart_type == "box":
                fig = px.box(plot_df, x=x_col, y=y_col, color=color_col, title=title)

            elif chart_type == "sunburst":
                path_cols = [x_col, color_col] if color_col else [x_col]
                fig = px.sunburst(plot_df, path=path_cols, values=y_col, title=title)

            elif chart_type == "funnel":
                fig = px.funnel(plot_df, x=y_col, y=x_col, title=title)

            elif chart_type == "table":
                fig = go.Figure(data=[go.Table(
                    header=dict(values=list(plot_df.columns), fill_color="#2c3e50", font_color="white"),
                    cells=dict(values=[plot_df[c].tolist() for c in plot_df.columns]),
                )])
                fig.update_layout(title=title)

            else:
                fig = px.bar(plot_df, x=x_col, y=y_col, title=title)

            fig.update_layout(
                template="plotly_white",
                font=dict(family="Inter, Arial, sans-serif", size=13),
                margin=dict(l=40, r=20, t=50, b=40),
            )
            return fig

        except Exception as e:
            logger.warning(f"Failed to build chart '{title}': {e}")
            empty = go.Figure()
            empty.update_layout(title=f"{title} (error: {e})")
            return empty

    def render(
        self,
        config_id: str,
        session_id: Optional[str] = None,
        export_formats: Optional[list[str]] = None,
    ) -> str:
        """
        Render the dashboard and return its URL path.
        """
        config = self._load_config(config_id)
        dashboard_url = f"/api/v1/dashboard/{config_id}"
        logger.info(f"Dashboard rendered: {dashboard_url}")
        return dashboard_url

    def render_to_html(self, config: dict) -> str:
        """
        Render the full dashboard as a self-contained HTML string.
        """
        csv_path = config.get("csv_path", "")
        title = config.get("title", "BioOracle Dashboard")
        description = config.get("description", "")
        charts = config.get("charts", [])

        try:
            df = self._load_data(csv_path)
        except Exception as e:
            return f"<html><body><h2>Error loading data: {e}</h2></body></html>"

        chart_htmls = []
        for chart in charts:
            fig = self._build_figure(chart, df)
            chart_html = fig.to_html(full_html=False, include_plotlyjs="cdn")
            chart_htmls.append(f'<div class="chart-container">{chart_html}</div>')

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  body {{ font-family: Inter, Arial, sans-serif; background: #f8fafc; margin: 0; padding: 20px; }}
  .header {{ background: #1e3a5f; color: white; padding: 24px 32px; border-radius: 8px; margin-bottom: 24px; }}
  .header h1 {{ margin: 0 0 8px 0; font-size: 1.8rem; }}
  .header p {{ margin: 0; opacity: 0.85; }}
  .charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(560px, 1fr)); gap: 20px; }}
  .chart-container {{ background: white; border-radius: 8px; padding: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); }}
  .footer {{ margin-top: 32px; text-align: center; color: #6b7280; font-size: 0.85rem; }}
</style>
</head>
<body>
  <div class="header">
    <h1>{title}</h1>
    <p>{description}</p>
  </div>
  <div class="charts-grid">
    {"".join(chart_htmls)}
  </div>
  <div class="footer">Generated by BioOracle</div>
</body>
</html>"""
        return html
