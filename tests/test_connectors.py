"""
Tests for API Connectors
Uses mocked HTTP responses to avoid live API calls during CI.
"""

from unittest.mock import MagicMock, patch

import pytest

from api.connectors.pubmed import PubMedConnector
from api.connectors.clinicaltrials import ClinicalTrialsConnector
from api.connectors.semantic_scholar import SemanticScholarConnector


class TestPubMedConnector:

    def test_parse_article_basic(self):
        connector = PubMedConnector()
        article = {
            "MedlineCitation": {
                "PMID": {"#text": "12345678"},
                "Article": {
                    "ArticleTitle": "Test Article Title",
                    "Journal": {
                        "Title": "Test Journal",
                        "JournalIssue": {
                            "PubDate": {"Year": "2023", "Month": "Jan"}
                        },
                    },
                    "Abstract": {"AbstractText": "This is an abstract."},
                    "AuthorList": {
                        "Author": [
                            {"LastName": "Smith", "ForeName": "John"},
                            {"LastName": "Doe", "ForeName": "Jane"},
                        ]
                    },
                },
                "MeshHeadingList": None,
            },
            "PubmedData": {"ArticleIdList": {"ArticleId": []}},
        }
        fields = ["pmid", "title", "date", "journal", "abstract", "authors", "mesh", "doi"]
        result = connector._parse_article(article, fields)

        assert result["pmid"] == "12345678"
        assert result["title"] == "Test Article Title"
        assert result["year"] == 2023
        assert result["journal"] == "Test Journal"
        assert "Smith" in result["authors"]
        assert result["author_count"] == 2

    def test_parse_article_missing_fields(self):
        connector = PubMedConnector()
        result = connector._parse_article({}, ["pmid", "title"])
        assert isinstance(result, dict)

    @patch("api.connectors.pubmed.requests.get")
    def test_esearch_returns_pmids(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "esearchresult": {"idlist": ["111", "222", "333"], "count": "3"}
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        connector = PubMedConnector()
        pmids = connector._esearch("diabetes", 10, None, None)
        assert pmids == ["111", "222", "333"]


class TestClinicalTrialsConnector:

    def test_parse_study_basic(self):
        connector = ClinicalTrialsConnector()
        study = {
            "protocolSection": {
                "identificationModule": {"nctId": "NCT12345678", "briefTitle": "Test Trial"},
                "statusModule": {"overallStatus": "RECRUITING"},
                "designModule": {"studyType": "INTERVENTIONAL", "phases": ["PHASE2"], "enrollmentInfo": {"count": 100}},
                "conditionsModule": {"conditions": ["Diabetes"]},
                "armsInterventionsModule": {"interventions": [{"name": "Drug A"}]},
                "contactsLocationsModule": {"locations": [{"country": "United States"}]},
                "sponsorCollaboratorsModule": {"leadSponsor": {"name": "NIH", "class": "NIH"}},
                "eligibilityModule": {"minimumAge": "18 Years", "maximumAge": "65 Years", "sex": "ALL"},
            }
        }
        result = connector._parse_study(study)
        assert result["nct_id"] == "NCT12345678"
        assert result["phase"] == "PHASE2"
        assert result["enrollment"] == 100
        assert "United States" in result["countries"]

    def test_parse_study_empty(self):
        connector = ClinicalTrialsConnector()
        result = connector._parse_study({})
        assert isinstance(result, dict)


class TestSemanticScholarConnector:

    @patch("api.connectors.semantic_scholar.requests.get")
    def test_fetch_returns_records(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {
                    "title": "AI in Medicine",
                    "year": 2023,
                    "citationCount": 150,
                    "venue": "Nature Medicine",
                    "isOpenAccess": True,
                    "authors": [{"name": "Alice"}],
                    "externalIds": {"DOI": "10.1000/test"},
                }
            ],
            "total": 1,
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        connector = SemanticScholarConnector()
        records = connector.fetch("AI medicine", max_results=5)
        assert len(records) == 1
        assert records[0]["citation_count"] == 150
        assert records[0]["title"] == "AI in Medicine"
