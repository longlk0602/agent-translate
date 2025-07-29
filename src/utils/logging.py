"""
Logging configuration for the translation agent
"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(
    log_level: int = logging.INFO, log_file: str = "translation_agent.log"
):
    """Setup logging for the translation agent"""

    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file) if os.path.dirname(log_file) else "."
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Create file handler with rotation
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Configure root logger
    logging.basicConfig(level=log_level, handlers=[console_handler, file_handler])

    # Set specific loggers
    logger = logging.getLogger("translation_agent")
    logger.setLevel(log_level)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(f"translation_agent.{name}")
