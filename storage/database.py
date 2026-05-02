"""
Database Connection and Session Management
SQLAlchemy setup for PostgreSQL.
"""

import os

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./biooracle_dev.db")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=os.getenv("ENV", "development") == "development",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables defined in models."""
    from storage import models
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized.")
