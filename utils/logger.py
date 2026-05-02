"""
Logger Configuration
Sets up Loguru with structured output for both console and file.
"""

import os
import sys

from loguru import logger


def configure_logger():
    """Configure Loguru logger for the application."""
    logger.remove()

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Console handler
    logger.add(
        sys.stdout,
        level=log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # File handler (optional, rotated daily)
    log_file = os.getenv("LOG_FILE", "./logs/biooracle.log")
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        logger.add(
            log_file,
            level=log_level,
            rotation="1 day",
            retention="7 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        )

    logger.info(f"Logger configured at level: {log_level}")
