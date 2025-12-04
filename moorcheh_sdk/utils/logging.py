import logging


def setup_logging(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.addHandler(logging.NullHandler())
    return logger
