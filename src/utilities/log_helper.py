"""Logging configuration for the application."""
import sys
import logging
from pathlib import Path
from loguru import logger
from src.utilities.settings import Settings

settings = Settings()

def setup_logging() -> None:
  """Configure logging for the application."""
  # Ensure log directory exists
  log_path = Path(settings.log_file)
  log_path.parent.mkdir(parents=True, exist_ok=True)

  # Remove all existing handlers
  logger.remove()

  fmt = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
  )

  # Add file logger
  logger.add(
    settings.log_file,
    level="DEBUG" if settings.verbose else "CRITICAL",
    format=fmt,
    rotation="1 MB",
    retention="1 day",
    enqueue=True,
  )

  # Add console logger
  logger.add(
    sys.stderr,
    level="DEBUG" if settings.verbose else "CRITICAL",
    format=fmt,
    enqueue=True,
  )

  # Configure standard library loggers
  logging.getLogger("ib_async").setLevel(logging.CRITICAL)
  logging.getLogger("httpx").setLevel(logging.WARNING)
  logging.getLogger("mcp").setLevel(logging.WARNING)
