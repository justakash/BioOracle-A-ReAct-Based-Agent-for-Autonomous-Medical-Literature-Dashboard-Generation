"""
MeSH Term Processor
Extracts, deduplicates, and ranks Medical Subject Headings from PubMed records.
"""

from collections import Counter
from typing import Optional

import pandas as pd
from loguru import logger


class MeSHProcessor:
    """
    Processes raw MeSH term strings from PubMed CSV exports.
    Provides frequency analysis and top-term extraction.
    """

    def __init__(self, delimiter: str = "; "):
        self.delimiter = delimiter

    def extract_all_terms(self, df: pd.DataFrame, column: str = "mesh_terms") -> list[str]:
        """Flatten all MeSH terms from a column into a single list."""
        if column not in df.columns:
            logger.warning(f"Column '{column}' not found in DataFrame.")
            return []

        all_terms = []
        for cell in df[column].dropna():
            terms = [t.strip() for t in str(cell).split(self.delimiter) if t.strip()]
            all_terms.extend(terms)

        return all_terms

    def get_term_frequencies(
        self,
        df: pd.DataFrame,
        column: str = "mesh_terms",
        top_n: Optional[int] = 30,
    ) -> pd.DataFrame:
        """
        Return a DataFrame of MeSH term frequencies.
        Columns: term, count, percentage
        """
        all_terms = self.extract_all_terms(df, column)
        if not all_terms:
            return pd.DataFrame(columns=["term", "count", "percentage"])

        counter = Counter(all_terms)
        total = sum(counter.values())

        rows = [
            {"term": term, "count": count, "percentage": round(count / total * 100, 2)}
            for term, count in counter.most_common(top_n)
        ]

        freq_df = pd.DataFrame(rows)
        logger.info(f"MeSH frequency analysis: {len(freq_df)} unique terms from {total} total mentions")
        return freq_df

    def get_term_trends(
        self,
        df: pd.DataFrame,
        top_terms: Optional[list[str]] = None,
        year_column: str = "year",
        mesh_column: str = "mesh_terms",
        top_n: int = 10,
    ) -> pd.DataFrame:
        """
        Return yearly frequency of top MeSH terms (for trend charts).
        Returns a long-format DataFrame: year, term, count
        """
        if year_column not in df.columns or mesh_column not in df.columns:
            logger.warning("Required columns missing for trend analysis.")
            return pd.DataFrame()

        if top_terms is None:
            freq_df = self.get_term_frequencies(df, mesh_column, top_n=top_n)
            top_terms = freq_df["term"].tolist()

        rows = []
        for _, row in df.iterrows():
            year = row.get(year_column)
            mesh_str = str(row.get(mesh_column, ""))
            row_terms = set(t.strip() for t in mesh_str.split(self.delimiter) if t.strip())
            for term in top_terms:
                if term in row_terms:
                    rows.append({"year": year, "term": term, "count": 1})

        if not rows:
            return pd.DataFrame()

        trend_df = (
            pd.DataFrame(rows)
            .groupby(["year", "term"], as_index=False)["count"]
            .sum()
            .sort_values(["year", "count"], ascending=[True, False])
        )

        logger.info(f"MeSH trend analysis complete: {len(trend_df)} rows")
        return trend_df
