"""
Export endpoint - handles CSV, JSON, and PDF report downloads.
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional
from loguru import logger

from utils.exporter import export_csv, export_json, export_pdf

router = APIRouter()


class EmailExportRequest(BaseModel):
    csv_path: str
    config_id: str
    recipient_email: str
    subject: Optional[str] = "BioOracle Dashboard Report"


@router.get("/csv/{session_id}")
async def download_csv(session_id: str):
    """Download the raw dataset CSV for a session."""
    csv_path = os.path.join(os.getenv("DATA_DIR", "./data"), f"{session_id}.csv")
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="CSV file not found.")
    return FileResponse(csv_path, media_type="text/csv", filename=f"biooracle_{session_id}.csv")


@router.get("/json/{session_id}")
async def download_json(session_id: str):
    """Download the dataset as JSON."""
    csv_path = os.path.join(os.getenv("DATA_DIR", "./data"), f"{session_id}.csv")
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Data file not found.")
    json_bytes = export_json(csv_path)
    return StreamingResponse(
        iter([json_bytes]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=biooracle_{session_id}.json"},
    )


@router.get("/pdf/{config_id}")
async def download_pdf(config_id: str):
    """Generate and download a PDF report for a dashboard config."""
    try:
        pdf_path = export_pdf(config_id)
        return FileResponse(pdf_path, media_type="application/pdf", filename=f"biooracle_{config_id}.pdf")
    except Exception as e:
        logger.exception(f"PDF export failed for config {config_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/email")
async def email_report(request: EmailExportRequest):
    """Send a dashboard report via email."""
    from utils.emailer import send_report_email
    try:
        send_report_email(
            csv_path=request.csv_path,
            config_id=request.config_id,
            recipient=request.recipient_email,
            subject=request.subject,
        )
        return {"status": "ok", "message": f"Report sent to {request.recipient_email}"}
    except Exception as e:
        logger.exception(f"Email delivery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
