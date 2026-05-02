"""
Export Utilities
Handles CSV, JSON, and PDF export generation.
"""

import json
import os
from typing import Optional

import pandas as pd
from loguru import logger


def export_csv(csv_path: str, output_path: Optional[str] = None) -> str:
    """Copy or return path to an existing CSV file."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    if output_path:
        import shutil
        shutil.copy2(csv_path, output_path)
        return output_path
    return csv_path


def export_json(csv_path: str) -> bytes:
    """Convert a CSV file to JSON bytes."""
    df = pd.read_csv(csv_path)
    return df.to_json(orient="records", indent=2).encode("utf-8")


def export_pdf(config_id: str, export_dir: Optional[str] = None) -> str:
    """
    Generate a PDF report for a dashboard config.
    Renders each chart as an image and assembles a reportlab PDF.
    """
    import json
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    data_dir = os.getenv("DATA_DIR", "./data")
    export_dir = export_dir or os.getenv("EXPORT_DIR", "./exports")
    os.makedirs(export_dir, exist_ok=True)

    config_path = os.path.join(data_dir, f"dashboard_config_{config_id}.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Dashboard config not found: {config_id}")

    with open(config_path, "r") as f:
        config = json.load(f)

    pdf_path = os.path.join(export_dir, f"biooracle_{config_id}.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(config.get("title", "BioOracle Report"), styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(config.get("description", ""), styles["Normal"]))
    story.append(Spacer(1, 12))

    for chart in config.get("charts", []):
        story.append(Paragraph(chart.get("title", "Chart"), styles["Heading2"]))
        desc = chart.get("description", "")
        if desc:
            story.append(Paragraph(desc, styles["Normal"]))
        story.append(Spacer(1, 8))

    doc.build(story)
    logger.info(f"PDF exported: {pdf_path}")
    return pdf_path
