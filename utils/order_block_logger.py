import logging
import time
from typing import Union, Any
import colorlog

from utils.logger import CustomLogger, color_formatter, file_formatter


def create_ob_logger(symbol: str, timeframe: str) -> Union[CustomLogger, Any]:
    # Create another logger for detailed messages about forming order blocks
    order_block_logger: Union[CustomLogger, Any] = logging.getLogger('order_block_logger')
    order_block_logger.setLevel(logging.DEBUG)  # Set the logger's level to the lowest level

    # Create a console handler and set its level to INFO
    order_block_console_handler = logging.StreamHandler()
    order_block_console_handler.setLevel(logging.INFO)

    # Create a file handler and set its level to DEBUG
    current_time = time.strftime("%Y-%m-%d_%H-%M-%S")
    order_block_file_handler = logging.FileHandler(f'logs/ob_logs/order_blocks-{symbol}-{timeframe}-{current_time}.log')
    order_block_file_handler.setLevel(logging.DEBUG)

    # Set the formatters for the handlers
    order_block_console_handler.setFormatter(color_formatter)
    order_block_file_handler.setFormatter(file_formatter)

    # Add the handlers to the order block logger
    order_block_logger.addHandler(order_block_console_handler)
    order_block_logger.addHandler(order_block_file_handler)

    return order_block_logger
