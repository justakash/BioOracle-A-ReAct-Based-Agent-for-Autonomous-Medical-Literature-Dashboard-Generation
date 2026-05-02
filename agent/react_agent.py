"""
BioOracle ReAct Agent
Core reasoning and acting loop powered by Claude Sonnet.
"""

import json
import os
from typing import Any, Optional

import anthropic
from loguru import logger

from agent.tools import get_tool_definitions, handle_tool_call
from agent.prompt import SYSTEM_PROMPT


class BioOracleAgent:
    """
    ReAct-based agent that orchestrates the full pipeline from natural language
    query to dashboard configuration.

    The agent follows a strict role separation:
    - Agent: planner and configurator (never touches raw API data)
    - Python backend: executor and data engineer
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
        self.max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", 4096))
        self.tools = get_tool_definitions()
        self.max_iterations = 10

    def run(self, user_query: str, session_id: Optional[str] = None) -> dict[str, Any]:
        """
        Execute the ReAct loop for a given user query.

        Returns a dict with:
        - execution_plan: structured plan JSON
        - dashboard_config: chart specifications
        - csv_path: path to the generated dataset
        - schema: column summary of the dataset
        - status: success or error
        - messages: full conversation log
        """
        messages = [{"role": "user", "content": user_query}]
        iteration = 0
        result = {
            "status": "running",
            "execution_plan": None,
            "dashboard_config": None,
            "csv_path": None,
            "schema": None,
            "messages": messages,
            "session_id": session_id,
        }

        logger.info(f"Starting ReAct loop for query: {user_query[:80]}...")

        while iteration < self.max_iterations:
            iteration += 1
            logger.debug(f"ReAct iteration {iteration}")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=SYSTEM_PROMPT,
                tools=self.tools,
                messages=messages,
            )

            # Append assistant response to message history
            messages.append({"role": "assistant", "content": response.content})

            # Check stop condition
            if response.stop_reason == "end_turn":
                logger.info("Agent reached end_turn - pipeline complete.")
                result["status"] = "success"
                result["messages"] = messages
                # Extract final text summary
                for block in response.content:
                    if hasattr(block, "text"):
                        result["summary"] = block.text
                break

            # Process tool calls
            if response.stop_reason == "tool_use":
                tool_results = []

                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    tool_name = block.name
                    tool_input = block.input
                    tool_use_id = block.id

                    logger.info(f"Agent calling tool: {tool_name}")
                    logger.debug(f"Tool input: {json.dumps(tool_input, indent=2)}")

                    tool_output = handle_tool_call(tool_name, tool_input, result)

                    # Capture structured outputs from specific tools
                    if tool_name == "create_execution_plan":
                        result["execution_plan"] = tool_input
                    elif tool_name == "configure_dashboard":
                        result["dashboard_config"] = tool_input
                    elif tool_name == "get_csv_schema":
                        result["schema"] = tool_output.get("schema")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps(tool_output),
                    })

                messages.append({"role": "user", "content": tool_results})

        if iteration >= self.max_iterations:
            logger.warning("ReAct loop hit max iterations without completing.")
            result["status"] = "max_iterations_reached"

        result["messages"] = messages
        return result
