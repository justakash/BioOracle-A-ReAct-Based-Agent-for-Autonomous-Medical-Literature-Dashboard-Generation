"""
SQLAlchemy ORM Models
Defines the persistent data schema for BioOracle.
"""

import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String, Text

from storage.database import Base


class QueryHistory(Base):
    """Stores every user query and its pipeline outcome."""

    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    query_text = Column(Text, nullable=False)
    intent = Column(String(64))
    sources_used = Column(JSON)
    status = Column(String(32), default="running")
    csv_path = Column(String(512))
    dashboard_config_id = Column(String(32))
    summary = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)


class DatasetRecord(Base):
    """Metadata about each generated dataset CSV."""

    __tablename__ = "dataset_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), index=True)
    source = Column(String(32))
    csv_path = Column(String(512))
    row_count = Column(Integer)
    column_names = Column(JSON)
    schema_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class DashboardConfig(Base):
    """Stores rendered dashboard configurations."""

    __tablename__ = "dashboard_configs"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(String(32), unique=True, index=True)
    session_id = Column(String(64), index=True)
    title = Column(String(255))
    config_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    view_count = Column(Integer, default=0)


class ExportRecord(Base):
    """Tracks all file exports for audit and download purposes."""

    __tablename__ = "export_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), index=True)
    export_format = Column(String(16))
    file_path = Column(String(512))
    file_size_bytes = Column(Integer)
    email_sent_to = Column(String(255))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
