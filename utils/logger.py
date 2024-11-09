import logging
from typing import Union, Any

import colorlog
import time


class CustomLogger(logging.Logger):
    def insert_blank_line(self):
        for handler in self.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.stream.write("\n")
                handler.flush()


# Set the custom logger class as the default logger class
logging.setLoggerClass(CustomLogger)

# Create a logger
logger: Union[CustomLogger, Any] = logging.getLogger('channel_logger')
logger.setLevel(logging.DEBUG)  # Set the logger's level to the lowest level

# Create a console handler and set its level to INFO
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create a file handler and set its level to DEBUG
current_time = time.strftime("%Y-%m-%d_%H-%M-%S")
file_handler = logging.FileHandler(f'logs/logs-{current_time}.log')
file_handler.setLevel(logging.DEBUG)

# Create a color formatter for the console handler
color_formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
)

# Create a standard formatter for the file handler
file_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)

# Set the formatters for the handlers
console_handler.setFormatter(color_formatter)
file_handler.setFormatter(file_formatter)

# Add the handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)


