"""
Logging configuration module
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logging(log_dir: Path, level: str = "INFO") -> None:
    """Configure logging system

    Args:
        log_dir: Log directory
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    # Log format
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Application named logger (avoid polluting global root logger)
    app_logger = logging.getLogger("mental_hospital")
    app_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers
    app_logger.handlers.clear()
    app_logger.propagate = False

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    app_logger.addHandler(console_handler)

    # File handler (rotating, max 10MB, keep 5 backups)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    app_logger.addHandler(file_handler)

    app_logger.info(f"Logging system initialized, log file: {log_file}")
