"""
Dashboard endpoint - serves rendered Plotly Dash dashboards.
"""

import json
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from loguru import logger

from dashboard.renderer import DashboardRenderer

router = APIRouter()


@router.get("/{config_id}", response_class=HTMLResponse)
async def get_dashboard(config_id: str):
    """
    Render and return an interactive Plotly Dash dashboard by config ID.
    """
    config_path = os.path.join(os.getenv("DATA_DIR", "./data"), f"dashboard_config_{config_id}.json")

    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail=f"Dashboard config '{config_id}' not found.")

    try:
        with open(config_path, "r") as f:
            config = json.load(f)

        renderer = DashboardRenderer()
        html = renderer.render_to_html(config)
        return HTMLResponse(content=html)
    except Exception as e:
        logger.exception(f"Failed to render dashboard {config_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{config_id}/config")
async def get_dashboard_config(config_id: str):
    """
    Return the raw dashboard configuration JSON.
    """
    config_path = os.path.join(os.getenv("DATA_DIR", "./data"), f"dashboard_config_{config_id}.json")

    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail=f"Dashboard config '{config_id}' not found.")

    with open(config_path, "r") as f:
        return json.load(f)
