# utils/app_logger.py

import logging
from logging import Logger

# -----------------------------
# Global Logging Config
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

def get_logger(name: str) -> Logger:
    """
    Returns a named logger with standard formatting.
    
    Example:
        logger = get_logger("PatientAuditor")
        logger.info("Started processing")
    """
    return logging.getLogger(name)
