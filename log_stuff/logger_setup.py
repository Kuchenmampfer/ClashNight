import logging
from .webhook_handler import WebhookHandler

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')


def setup_logger(name, log_file, webhook_url, level):
    """To setup as many loggers as you want"""

    stream_handler = logging.StreamHandler()  # this handler will log to stderr
    file_handler = logging.FileHandler(filename=log_file, encoding='utf-8', mode='w')
    webhook_handler = WebhookHandler(webhook_url=webhook_url, level=logging.WARNING)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    for handler in [stream_handler, file_handler, webhook_handler]:
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
