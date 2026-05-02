"""
Chart Builder
Standalone helper functions for building standard biomedical Plotly charts.
Can be called directly without a full dashboard config.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from loguru import logger


def publications_per_year(df: pd.DataFrame, year_col: str = "year") -> go.Figure:
    """Line chart of publication count by year."""
    counts = df[year_col].value_counts().reset_index()
    counts.columns = ["year", "publications"]
    counts = counts.sort_values("year")
    fig = px.line(counts, x="year", y="publications",
                  title="Publications Per Year", markers=True,
                  template="plotly_white")
    fig.update_traces(line_color="#2980b9", line_width=2.5)
    return fig


def top_journals(df: pd.DataFrame, journal_col: str = "journal", top_n: int = 15) -> go.Figure:
    """Horizontal bar chart of top journals by publication count."""
    counts = df[journal_col].value_counts().head(top_n).reset_index()
    counts.columns = ["journal", "count"]
    counts = counts.sort_values("count")
    fig = px.bar(counts, x="count", y="journal", orientation="h",
                 title=f"Top {top_n} Journals", template="plotly_white",
                 color="count", color_continuous_scale="Blues")
    fig.update_layout(showlegend=False, coloraxis_showscale=False)
    return fig


def top_mesh_terms(df: pd.DataFrame, mesh_col: str = "mesh_terms", top_n: int = 20) -> go.Figure:
    """Treemap of top MeSH terms by frequency."""
    from etl.mesh_processor import MeSHProcessor
    processor = MeSHProcessor()
    freq_df = processor.get_term_frequencies(df, column=mesh_col, top_n=top_n)
    if freq_df.empty:
        fig = go.Figure()
        fig.update_layout(title="No MeSH terms available")
        return fig
    fig = px.treemap(freq_df, path=["term"], values="count",
                     title=f"Top {top_n} MeSH Terms", template="plotly_white",
                     color="count", color_continuous_scale="Teal")
    return fig


def top_authors(df: pd.DataFrame, author_col: str = "first_author", top_n: int = 15) -> go.Figure:
    """Bar chart of most prolific first authors."""
    counts = df[author_col].value_counts().head(top_n).reset_index()
    counts.columns = ["author", "publications"]
    counts = counts.sort_values("publications")
    fig = px.bar(counts, x="publications", y="author", orientation="h",
                 title=f"Top {top_n} Authors by Publications", template="plotly_white",
                 color="publications", color_continuous_scale="Purples")
    fig.update_layout(showlegend=False, coloraxis_showscale=False)
    return fig


def trial_phase_distribution(df: pd.DataFrame, phase_col: str = "phase") -> go.Figure:
    """Donut chart of clinical trial phase distribution."""
    counts = df[phase_col].value_counts().reset_index()
    counts.columns = ["phase", "count"]
    fig = px.pie(counts, names="phase", values="count",
                 title="Trial Phase Distribution", hole=0.4,
                 template="plotly_white",
                 color_discrete_sequence=px.colors.sequential.RdBu)
    return fig


def trial_status_chart(df: pd.DataFrame, status_col: str = "status") -> go.Figure:
    """Bar chart of trial status breakdown."""
    counts = df[status_col].value_counts().reset_index()
    counts.columns = ["status", "count"]
    fig = px.bar(counts, x="status", y="count",
                 title="Trials by Status", template="plotly_white",
                 color="count", color_continuous_scale="Greens")
    fig.update_layout(showlegend=False, coloraxis_showscale=False)
    return fig


def geographic_distribution(df: pd.DataFrame, country_col: str = "countries") -> go.Figure:
    """Choropleth world map of trial or publication geographic spread."""
    from collections import Counter
    all_countries = []
    for cell in df[country_col].dropna():
        all_countries.extend([c.strip() for c in str(cell).split(";") if c.strip()])

    counter = Counter(all_countries)
    geo_df = pd.DataFrame(counter.items(), columns=["country", "count"])
    fig = px.choropleth(geo_df, locations="country", color="count",
                        locationmode="country names",
                        title="Geographic Distribution",
                        color_continuous_scale="Blues",
                        template="plotly_white")
    return fig


def citation_scatter(df: pd.DataFrame, year_col: str = "year",
                     citation_col: str = "citation_count") -> go.Figure:
    """Scatter plot of citation count vs publication year."""
    fig = px.scatter(df, x=year_col, y=citation_col,
                     title="Citations vs Publication Year",
                     template="plotly_white",
                     opacity=0.6, color=citation_col,
                     color_continuous_scale="Reds")
    return fig
