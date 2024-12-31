import requests
import time

import utils.constants as constants
from utils.logger import logger


def post_message(message: str, reply_id: int = None):
    """
    Post a message to the channel

    Args:
        message (str): The message to post
        reply_id (int): The id of the message to reply to, if any

    Returns:
        int: The id of the message that was posted
    """

    payload = {
        "chat_id": constants.channel_id,
        "text": message,
        "reply_to_message_id": reply_id
    }

    while True:
        response = requests.post(
            f'https://api.telegram.org/bot{constants.credentials["BOT_TOKEN"]}/sendMessage', json=payload).json()

        if response.get("ok"):
            time.sleep(3)
            return response["result"]["message_id"]

        else:
            logger.error(f"Failed to post message: {response['description']}. Retrying...")


def get_channel_name(channel_id: int):
    """
    Get the name of the channel
    Args:
        channel_id (int): The id of the channel

    Returns:
        str: The name of the channel
    """
    url = f'https://api.telegram.org/bot{constants.credentials["BOT_TOKEN"]}/getChat'
    params = {"chat_id": channel_id}
    response = requests.get(url, params=params).json()

    if response["ok"]:
        return response["result"]["title"]
    else:
        raise Exception(f"Error getting channel name: {response['description']}")
