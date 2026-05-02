"""
Tests for the BioOracle ReAct Agent
Uses mocked Anthropic client to avoid API charges.
"""

from unittest.mock import MagicMock, patch

import pytest

from agent.react_agent import BioOracleAgent
from agent.prompt import SYSTEM_PROMPT


class TestBioOracleAgent:

    def test_system_prompt_not_empty(self):
        assert len(SYSTEM_PROMPT) > 100

    def test_system_prompt_contains_key_instructions(self):
        assert "ReAct" in SYSTEM_PROMPT
        assert "create_execution_plan" in SYSTEM_PROMPT
        assert "render_dashboard" in SYSTEM_PROMPT

    @patch("agent.react_agent.anthropic.Anthropic")
    def test_agent_initializes(self, mock_anthropic_class):
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        agent = BioOracleAgent()
        assert agent.max_iterations == 10
        assert agent.tools is not None

    @patch("agent.react_agent.anthropic.Anthropic")
    def test_agent_run_end_turn(self, mock_anthropic_class):
        """Test that agent exits cleanly on end_turn."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="Dashboard ready.", spec=["text"])]
        mock_client.messages.create.return_value = mock_response

        agent = BioOracleAgent()
        result = agent.run("Show me diabetes trends", session_id="test-001")

        assert result["status"] == "success"
        assert result["summary"] == "Dashboard ready."

    @patch("agent.react_agent.anthropic.Anthropic")
    def test_agent_max_iterations_reached(self, mock_anthropic_class):
        """Test that agent stops after max_iterations."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.stop_reason = "tool_use"
        mock_block = MagicMock()
        mock_block.type = "tool_use"
        mock_block.name = "create_execution_plan"
        mock_block.input = {"intent": "research_trends"}
        mock_block.id = "tu_001"
        mock_response.content = [mock_block]
        mock_client.messages.create.return_value = mock_response

        agent = BioOracleAgent()
        agent.max_iterations = 2

        with patch("agent.tools.handle_tool_call", return_value={"status": "ok"}):
            result = agent.run("Infinite loop query")

        assert result["status"] == "max_iterations_reached"
