"""
Tests for ETL Pipeline and Schema Inspector
"""

import os
import tempfile

import pandas as pd
import pytest

from etl.pipeline import ETLPipeline
from etl.schema_inspector import inspect_csv_schema
from etl.mesh_processor import MeSHProcessor


class TestETLPipeline:

    def setup_method(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.pipeline = ETLPipeline()
        self.pipeline.data_dir = self.tmp_dir

    def test_process_pubmed_records(self):
        records = [
            {"pmid": "1", "title": "Study A", "year": 2022, "journal": "Journal A",
             "authors": "Smith, J; Doe, J", "author_count": 2, "first_author": "Smith, J",
             "mesh_terms": "Diabetes; Insulin"},
            {"pmid": "2", "title": "Study B", "year": 2023, "journal": "Journal B",
             "authors": "Lee, K", "author_count": 1, "first_author": "Lee, K",
             "mesh_terms": "Hypertension"},
        ]
        csv_path = self.pipeline.process(records, source="pubmed", session_id="test_pubmed")
        assert os.path.exists(csv_path)
        df = pd.read_csv(csv_path)
        assert len(df) == 2
        assert "year" in df.columns

    def test_process_empty_records(self):
        csv_path = self.pipeline.process([], source="pubmed", session_id="test_empty")
        assert os.path.exists(csv_path)

    def test_process_clinicaltrials_records(self):
        records = [
            {"nct_id": "NCT001", "title": "Trial A", "status": "RECRUITING",
             "phase": "PHASE2", "enrollment": 100, "conditions": "Diabetes",
             "interventions": "Drug A", "countries": "United States", "sponsor": "NIH",
             "sponsor_class": "NIH", "min_age": "18 Years", "max_age": "65 Years",
             "gender": "ALL", "location_count": 5, "country_count": 1},
        ]
        csv_path = self.pipeline.process(records, source="clinicaltrials", session_id="test_ct")
        df = pd.read_csv(csv_path)
        assert len(df) == 1
        assert "nct_id" in df.columns

    def test_deduplication_on_pmid(self):
        records = [
            {"pmid": "42", "title": "Dup Study", "year": 2021, "journal": "J1",
             "authors": "A", "author_count": 1, "first_author": "A"},
            {"pmid": "42", "title": "Dup Study Copy", "year": 2021, "journal": "J1",
             "authors": "A", "author_count": 1, "first_author": "A"},
        ]
        csv_path = self.pipeline.process(records, source="pubmed", session_id="test_dedup")
        df = pd.read_csv(csv_path)
        assert len(df) == 1


class TestSchemaInspector:

    def test_inspect_valid_csv(self, tmp_path):
        csv_path = str(tmp_path / "test.csv")
        df = pd.DataFrame({
            "year": [2020, 2021, 2022],
            "journal": ["J1", "J2", "J3"],
            "citation_count": [10, 20, 30],
        })
        df.to_csv(csv_path, index=False)

        schema = inspect_csv_schema(csv_path)
        assert schema["row_count"] == 3
        assert schema["column_count"] == 3
        col_names = [c["name"] for c in schema["columns"]]
        assert "year" in col_names
        assert "citation_count" in col_names

    def test_inspect_missing_file(self):
        schema = inspect_csv_schema("/nonexistent/path.csv")
        assert "error" in schema


class TestMeSHProcessor:

    def test_term_frequencies(self):
        df = pd.DataFrame({
            "mesh_terms": [
                "Diabetes; Insulin; Glucose",
                "Diabetes; Hypertension",
                "Insulin; Glucose",
            ]
        })
        processor = MeSHProcessor()
        freq_df = processor.get_term_frequencies(df, top_n=10)
        assert not freq_df.empty
        top_term = freq_df.iloc[0]["term"]
        assert top_term in ["Diabetes", "Insulin", "Glucose"]

    def test_empty_mesh_column(self):
        df = pd.DataFrame({"other_col": ["a", "b"]})
        processor = MeSHProcessor()
        terms = processor.extract_all_terms(df, column="mesh_terms")
        assert terms == []
