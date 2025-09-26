import logging
import os

from rich.logging import RichHandler

LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
LOG_LEVEL_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a logger instance with the specified name.
    The level of the logger is set based on the LOG_LEVEL environment variable.
    If not set, the default level is 'info'.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logging.basicConfig(
        level=LOG_LEVEL_MAP[LOG_LEVEL],
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(markup=True)],
    )

    return logging.getLogger(name)
