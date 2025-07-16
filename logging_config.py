import logging
import sys
from pythonjsonlogger import jsonlogger

def configure_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    log_handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s')
    log_handler.setFormatter(formatter)

    logger.handlers = []
    logger.addHandler(log_handler)
