import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger

def setup_logger(name="app"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Ensure logs directory exists
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # File Handler - JSON Format for production traceability
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, f"{name}.log"), maxBytes=10*1024*1024, backupCount=5
    )
    json_formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)

    # Console Handler - Standard Format
    console_handler = logging.StreamHandler(sys.stdout)
    standard_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(standard_formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    return logger

app_logger = setup_logger()
