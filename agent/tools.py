"""
Tool definitions and handlers for the BioOracle ReAct agent.
All tools follow strict schemas so the agent cannot hallucinate API parameters.
"""

from typing import Any

from loguru import logger


def get_tool_definitions() -> list[dict]:
    """Return Claude tool schemas for the ReAct agent."""
    return [
        {
            "name": "create_execution_plan",
            "description": (
                "Step 1: Analyze the user query and create a structured execution plan. "
                "Call this first before any data fetching."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "intent": {
                        "type": "string",
                        "enum": [
                            "research_trends",
                            "clinical_trials",
                            "journal_analysis",
                            "author_analysis",
                            "keyword_analysis",
                            "geographic_analysis",
                            "citation_analysis",
                            "comparative_analysis",
                        ],
                        "description": "Classified intent of the user query.",
                    },
                    "sources": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["pubmed", "clinicaltrials", "semantic_scholar", "europe_pmc"],
                        },
                        "description": "Which APIs to query.",
                    },
                    "search_terms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of search queries to run.",
                    },
                    "date_range": {
                        "type": "object",
                        "properties": {
                            "from_year": {"type": "integer"},
                            "to_year": {"type": "integer"},
                        },
                        "description": "Year range filter. Omit if not applicable.",
                    },
                    "expected_metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Metrics to extract e.g. publications_per_year, top_journals.",
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of why you chose these sources and queries.",
                    },
                },
                "required": ["intent", "sources", "search_terms", "expected_metrics", "reasoning"],
            },
        },
        {
            "name": "fetch_pubmed_data",
            "description": (
                "Step 2a: Fetch publication data from PubMed/NCBI. "
                "The backend handles all API calls, XML parsing, and CSV creation. "
                "Returns a csv_path and basic schema summary."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Valid PubMed search query string.",
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 500,
                        "description": "Max number of records to retrieve (max 5000).",
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date YYYY/MM/DD format.",
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date YYYY/MM/DD format.",
                    },
                    "fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["title", "abstract", "mesh", "authors", "date", "journal", "pmid", "doi"],
                        },
                        "description": "Fields to extract.",
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session ID for caching.",
                    },
                },
                "required": ["query", "fields"],
            },
        },
        {
            "name": "fetch_clinicaltrials_data",
            "description": (
                "Step 2b: Fetch clinical trial data from ClinicalTrials.gov. "
                "Returns a csv_path and schema."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "condition": {
                        "type": "string",
                        "description": "Medical condition to search for.",
                    },
                    "intervention": {
                        "type": "string",
                        "description": "Drug or intervention name (optional).",
                    },
                    "status": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["RECRUITING", "COMPLETED", "ACTIVE_NOT_RECRUITING", "NOT_YET_RECRUITING"],
                        },
                        "description": "Trial status filter (optional).",
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 200,
                    },
                    "session_id": {"type": "string"},
                },
                "required": ["condition"],
            },
        },
        {
            "name": "fetch_semantic_scholar_data",
            "description": "Step 2c: Fetch citation and paper data from Semantic Scholar.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query."},
                    "max_results": {"type": "integer", "default": 100},
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields: title, year, citationCount, authors, venue.",
                    },
                    "session_id": {"type": "string"},
                },
                "required": ["query"],
            },
        },
        {
            "name": "get_csv_schema",
            "description": (
                "Step 3: Inspect the schema of a generated CSV file. "
                "Returns column names, types, row count, and sample values. "
                "Call this after fetching data, before configuring the dashboard."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "csv_path": {
                        "type": "string",
                        "description": "Path to the CSV file returned by a fetch tool.",
                    }
                },
                "required": ["csv_path"],
            },
        },
        {
            "name": "configure_dashboard",
            "description": (
                "Step 4: Define the dashboard layout and chart specifications based on the CSV schema. "
                "The backend will use this config to render the final Plotly Dash dashboard."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Dashboard title.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Brief description of what this dashboard shows.",
                    },
                    "csv_path": {
                        "type": "string",
                        "description": "Path to the dataset CSV.",
                    },
                    "charts": {
                        "type": "array",
                        "description": "List of chart specifications.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "chart_id": {"type": "string"},
                                "chart_type": {
                                    "type": "string",
                                    "enum": [
                                        "line", "bar", "scatter", "pie", "donut",
                                        "treemap", "heatmap", "choropleth", "histogram",
                                        "box", "sunburst", "funnel", "table",
                                    ],
                                },
                                "title": {"type": "string"},
                                "x_column": {"type": "string"},
                                "y_column": {"type": "string"},
                                "color_column": {"type": "string"},
                                "aggregation": {
                                    "type": "string",
                                    "enum": ["count", "sum", "mean", "median", "max", "min"],
                                },
                                "top_n": {"type": "integer", "description": "Limit to top N results."},
                                "description": {"type": "string"},
                            },
                            "required": ["chart_id", "chart_type", "title"],
                        },
                    },
                    "filters": {
                        "type": "array",
                        "description": "Interactive filter controls for the dashboard.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "filter_id": {"type": "string"},
                                "filter_type": {
                                    "type": "string",
                                    "enum": ["year_range_slider", "dropdown", "multi_select", "text_search"],
                                },
                                "column": {"type": "string"},
                                "label": {"type": "string"},
                            },
                            "required": ["filter_id", "filter_type", "column", "label"],
                        },
                    },
                    "layout": {
                        "type": "string",
                        "enum": ["single_column", "two_column", "grid_2x2", "grid_3x2"],
                        "description": "Visual layout of the dashboard.",
                    },
                },
                "required": ["title", "description", "csv_path", "charts"],
            },
        },
        {
            "name": "render_dashboard",
            "description": (
                "Step 5: Trigger the backend to render the Plotly Dash dashboard "
                "from the dashboard configuration. Returns the dashboard URL."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "dashboard_config_id": {
                        "type": "string",
                        "description": "ID of the dashboard configuration to render.",
                    },
                    "session_id": {"type": "string"},
                    "export_formats": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["csv", "json", "pdf"]},
                        "description": "Export formats to make available for download.",
                    },
                },
                "required": ["dashboard_config_id"],
            },
        },
    ]


def handle_tool_call(tool_name: str, tool_input: dict, agent_result: dict) -> dict[str, Any]:
    """
    Route a tool call from the agent to the appropriate backend handler.
    Returns the tool result as a dict.
    """
    from api.connectors.pubmed import PubMedConnector
    from api.connectors.clinicaltrials import ClinicalTrialsConnector
    from api.connectors.semantic_scholar import SemanticScholarConnector
    from etl.pipeline import ETLPipeline
    from etl.schema_inspector import inspect_csv_schema
    from dashboard.renderer import DashboardRenderer

    try:
        if tool_name == "create_execution_plan":
            logger.info(f"Execution plan created: intent={tool_input.get('intent')}")
            return {"status": "ok", "message": "Execution plan recorded. Proceed to data fetching."}

        elif tool_name == "fetch_pubmed_data":
            connector = PubMedConnector()
            etl = ETLPipeline()
            raw_data = connector.fetch(
                query=tool_input["query"],
                max_results=tool_input.get("max_results", 500),
                date_from=tool_input.get("date_from"),
                date_to=tool_input.get("date_to"),
                fields=tool_input.get("fields", ["title", "date", "journal", "mesh", "authors"]),
            )
            csv_path = etl.process(raw_data, source="pubmed", session_id=tool_input.get("session_id"))
            agent_result["csv_path"] = csv_path
            schema = inspect_csv_schema(csv_path)
            return {"status": "ok", "csv_path": csv_path, "schema_summary": schema}

        elif tool_name == "fetch_clinicaltrials_data":
            connector = ClinicalTrialsConnector()
            etl = ETLPipeline()
            raw_data = connector.fetch(
                condition=tool_input["condition"],
                intervention=tool_input.get("intervention"),
                status=tool_input.get("status"),
                max_results=tool_input.get("max_results", 200),
            )
            csv_path = etl.process(raw_data, source="clinicaltrials", session_id=tool_input.get("session_id"))
            agent_result["csv_path"] = csv_path
            schema = inspect_csv_schema(csv_path)
            return {"status": "ok", "csv_path": csv_path, "schema_summary": schema}

        elif tool_name == "fetch_semantic_scholar_data":
            connector = SemanticScholarConnector()
            etl = ETLPipeline()
            raw_data = connector.fetch(
                query=tool_input["query"],
                max_results=tool_input.get("max_results", 100),
                fields=tool_input.get("fields", ["title", "year", "citationCount", "authors"]),
            )
            csv_path = etl.process(raw_data, source="semantic_scholar", session_id=tool_input.get("session_id"))
            agent_result["csv_path"] = csv_path
            schema = inspect_csv_schema(csv_path)
            return {"status": "ok", "csv_path": csv_path, "schema_summary": schema}

        elif tool_name == "get_csv_schema":
            schema = inspect_csv_schema(tool_input["csv_path"])
            return {"status": "ok", "schema": schema}

        elif tool_name == "configure_dashboard":
            import json, hashlib, os
            config_str = json.dumps(tool_input)
            config_id = hashlib.md5(config_str.encode()).hexdigest()[:8]
            config_path = os.path.join(os.getenv("DATA_DIR", "./data"), f"dashboard_config_{config_id}.json")
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w") as f:
                f.write(config_str)
            agent_result["dashboard_config_id"] = config_id
            return {"status": "ok", "dashboard_config_id": config_id, "message": "Config saved. Call render_dashboard next."}

        elif tool_name == "render_dashboard":
            renderer = DashboardRenderer()
            config_id = tool_input["dashboard_config_id"]
            dashboard_url = renderer.render(
                config_id=config_id,
                session_id=tool_input.get("session_id"),
                export_formats=tool_input.get("export_formats", ["csv"]),
            )
            return {"status": "ok", "dashboard_url": dashboard_url}

        else:
            logger.warning(f"Unknown tool call: {tool_name}")
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}

    except Exception as e:
        logger.exception(f"Tool {tool_name} failed: {e}")
        return {"status": "error", "message": str(e)}
