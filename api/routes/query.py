"""
Query endpoint - accepts natural language queries and runs the ReAct agent pipeline.
"""

import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from loguru import logger

from agent.react_agent import BioOracleAgent

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    async_mode: bool = False


class QueryResponse(BaseModel):
    session_id: str
    status: str
    summary: Optional[str] = None
    dashboard_url: Optional[str] = None
    csv_path: Optional[str] = None
    execution_plan: Optional[dict] = None


@router.post("/", response_model=QueryResponse)
async def run_query(request: QueryRequest):
    """
    Accept a natural language biomedical query and return a dashboard.
    """
    session_id = request.session_id or str(uuid.uuid4())
    logger.info(f"Received query for session {session_id}: {request.query[:80]}")

    try:
        agent = BioOracleAgent()
        result = agent.run(user_query=request.query, session_id=session_id)

        dashboard_url = None
        if result.get("dashboard_config"):
            dashboard_url = f"/api/v1/dashboard/{result.get('dashboard_config_id', '')}"

        return QueryResponse(
            session_id=session_id,
            status=result.get("status", "unknown"),
            summary=result.get("summary"),
            dashboard_url=dashboard_url,
            csv_path=result.get("csv_path"),
            execution_plan=result.get("execution_plan"),
        )
    except Exception as e:
        logger.exception(f"Query failed for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
