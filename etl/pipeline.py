"""
ETL Pipeline
Transforms raw API records into clean, normalized CSV files.
"""

import os
import uuid
from typing import Optional

import pandas as pd
from loguru import logger


class ETLPipeline:
    """
    Handles extraction, transformation, and loading for all data sources.
    Each source has a dedicated normalization method.
    """

    def __init__(self):
        self.data_dir = os.getenv("DATA_DIR", "./data")
        os.makedirs(self.data_dir, exist_ok=True)

    def process(
        self,
        records: list[dict],
        source: str,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Process raw records from any supported source into a clean CSV.
        Returns the path to the saved CSV file.
        """
        if not records:
            logger.warning(f"ETL received empty records for source={source}")
            df = pd.DataFrame()
        else:
            if source == "pubmed":
                df = self._normalize_pubmed(records)
            elif source == "clinicaltrials":
                df = self._normalize_clinicaltrials(records)
            elif source == "semantic_scholar":
                df = self._normalize_semantic_scholar(records)
            elif source == "europe_pmc":
                df = self._normalize_europe_pmc(records)
            else:
                logger.warning(f"Unknown source '{source}', using raw records.")
                df = pd.DataFrame(records)

        session_id = session_id or str(uuid.uuid4())
        csv_path = os.path.join(self.data_dir, f"{session_id}.csv")
        df.to_csv(csv_path, index=False)
        logger.info(f"ETL complete: {len(df)} rows saved to {csv_path}")
        return csv_path

    def _normalize_pubmed(self, records: list[dict]) -> pd.DataFrame:
        df = pd.DataFrame(records)

        # Clean year column
        if "year" in df.columns:
            df["year"] = pd.to_numeric(df["year"], errors="coerce")
            df = df[df["year"].notna()]
            df["year"] = df["year"].astype(int)

        # Clean text columns
        for col in ["title", "journal", "abstract", "authors", "mesh_terms"]:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()

        # Deduplicate on pmid if present
        if "pmid" in df.columns:
            df = df.drop_duplicates(subset=["pmid"])

        df = df.sort_values("year", ascending=False) if "year" in df.columns else df
        logger.debug(f"PubMed normalization complete: {len(df)} rows")
        return df

    def _normalize_clinicaltrials(self, records: list[dict]) -> pd.DataFrame:
        df = pd.DataFrame(records)

        # Normalize enrollment to numeric
        if "enrollment" in df.columns:
            df["enrollment"] = pd.to_numeric(df["enrollment"], errors="coerce")

        # Standardize status values
        if "status" in df.columns:
            df["status"] = df["status"].str.replace("_", " ").str.title()

        # Deduplicate on nct_id
        if "nct_id" in df.columns:
            df = df.drop_duplicates(subset=["nct_id"])

        for col in ["title", "conditions", "interventions", "sponsor", "countries"]:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()

        logger.debug(f"ClinicalTrials normalization complete: {len(df)} rows")
        return df

    def _normalize_semantic_scholar(self, records: list[dict]) -> pd.DataFrame:
        df = pd.DataFrame(records)

        if "year" in df.columns:
            df["year"] = pd.to_numeric(df["year"], errors="coerce")

        if "citation_count" in df.columns:
            df["citation_count"] = pd.to_numeric(df["citation_count"], errors="coerce").fillna(0).astype(int)

        for col in ["title", "venue", "authors"]:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()

        df = df.sort_values("citation_count", ascending=False) if "citation_count" in df.columns else df
        logger.debug(f"Semantic Scholar normalization complete: {len(df)} rows")
        return df

    def _normalize_europe_pmc(self, records: list[dict]) -> pd.DataFrame:
        df = pd.DataFrame(records)

        if "year" in df.columns:
            df["year"] = pd.to_numeric(df["year"], errors="coerce")

        if "citation_count" in df.columns:
            df["citation_count"] = pd.to_numeric(df["citation_count"], errors="coerce").fillna(0).astype(int)

        for col in ["title", "journal", "authors", "abstract", "keywords"]:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()

        if "pmid" in df.columns:
            df = df.drop_duplicates(subset=["pmid"])

        logger.debug(f"Europe PMC normalization complete: {len(df)} rows")
        return df
