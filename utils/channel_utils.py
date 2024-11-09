import requests

import utils.constants as constants


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
        "chat_id": constants.credentials["CHANNEL_ID"],
        "text": message,
        "reply_to_message_id": reply_id
    }
    response = requests.post(
        f'https://api.telegram.org/bot{constants.credentials["BOT_TOKEN"]}/sendMessage', json=payload).json()

    return response["result"]["message_id"]


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
