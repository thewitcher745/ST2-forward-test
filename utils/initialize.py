import logging

from utils.channel_utils import get_channel_name
from algo_code.general_utils import get_pair_list
import utils.constants as constants
from utils.logger import console_handler, logger


def set_console_logging_level():
    """
    Sets the logging level of the console handler based on the mode the program is running in.
    """
    if constants.mode == "DEV":
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.WARNING)


def declare_start(channel_name: str):
    """
    Logs a message saying that the program is starting on a specific channel.

    Args:
        channel_name (str): The name of the channel the program is starting on.
    """
    logger.info(f"Starting on channel {channel_name}...")


def confirm_start(channel_name):
    """
    Confirms the channel and pair list before starting the program.

    Args:
        channel_name (str): The name of the channel the program is starting on.
    """

    print(
        f"About to post to the channel with name {channel_name}. To confirm the channel and pair list type y...")
    confirmation_input = input("Enter your response: ")

    if confirmation_input.lower() not in ["y", "yes"]:
        quit()
    else:
        declare_start(channel_name)


def initiate_pair_list() -> list:
    pair_list = get_pair_list(constants.pair_list_filename)
    logger.info("Pair list to run is:")
    for pair in pair_list:
        logger.info(f"| {pair}")

    logger.insert_blank_line()

    return pair_list


def initialize():
    """
    Initializes the program by setting the console logging level and confirming the start (if the mode is not DEV).
    """

    set_console_logging_level()

    channel_name = get_channel_name(constants.credentials["CHANNEL_ID"])

    if constants.mode != "DEV":
        confirm_start(channel_name)
    else:
        logger.info("STARTING IN DEV MODE")
        declare_start(channel_name)
