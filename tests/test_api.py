"""
Tests for FastAPI endpoints using TestClient.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.server import app

client = TestClient(app)


class TestHealthEndpoint:

    def test_health_ok(self):
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestQueryEndpoint:

    @patch("api.routes.query.BioOracleAgent")
    def test_run_query_success(self, mock_agent_class):
        mock_agent = MagicMock()
        mock_agent.run.return_value = {
            "status": "success",
            "summary": "Dashboard for diabetes research.",
            "csv_path": "./data/test_session.csv",
            "execution_plan": {"intent": "research_trends"},
            "dashboard_config": {"title": "Test"},
            "dashboard_config_id": "abc12345",
        }
        mock_agent_class.return_value = mock_agent

        response = client.post(
            "/api/v1/query/",
            json={"query": "Show me diabetes research trends", "session_id": "test-session-001"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "session_id" in data

    @patch("api.routes.query.BioOracleAgent")
    def test_run_query_agent_error(self, mock_agent_class):
        mock_agent = MagicMock()
        mock_agent.run.side_effect = Exception("Agent pipeline failed")
        mock_agent_class.return_value = mock_agent

        response = client.post(
            "/api/v1/query/",
            json={"query": "This will fail"},
        )
        assert response.status_code == 500


class TestDashboardEndpoint:

    def test_dashboard_not_found(self):
        response = client.get("/api/v1/dashboard/nonexistentconfig")
        assert response.status_code == 404

    def test_dashboard_config_not_found(self):
        response = client.get("/api/v1/dashboard/nonexistentconfig/config")
        assert response.status_code == 404


class TestExportEndpoint:

    def test_csv_not_found(self):
        response = client.get("/api/v1/export/csv/nonexistent-session")
        assert response.status_code == 404

    def test_json_not_found(self):
        response = client.get("/api/v1/export/json/nonexistent-session")
        assert response.status_code == 404
