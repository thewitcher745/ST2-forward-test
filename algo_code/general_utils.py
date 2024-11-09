import datetime
import time
import requests
from binance.client import Client
from binance.enums import HistoricalKlinesType
import pandas as pd
import json

from utils import constants


def get_pair_data(client: Client, symbol: str, num_candles: int) -> pd.DataFrame:
    """
    Fetch the last N historical kline data for a given symbol and return it as a DataFrame.

    Args:
        client (Client): Binance API client.
        symbol (str): Trading pair symbol.
        num_candles (int): Number of candles to fetch from server

    Returns:
        pd.DataFrame: DataFrame containing the historical kline data.
    """

    # 20 has to be added for whatever reason. It just works!
    num_candles += 20

    # Calculate the start time based on the current time and the number of candles
    end_time = int(time.time() * 1000)  # Current time in milliseconds
    timeframe_seconds = pd.Timedelta(constants.timeframe).total_seconds()
    start_time = end_time - (num_candles * int(timeframe_seconds * 1000))

    try:
        # Fetch historical kline data
        response = client.get_historical_klines(symbol, constants.timeframe, start_str=start_time, end_str=end_time,
                                                klines_type=HistoricalKlinesType.FUTURES)
    except Exception as e:
        raise RuntimeError(f"Error fetching historical klines: {e}")

    # Convert UNIX timestamp to UTC time format and create DataFrame
    data = [[datetime.datetime.utcfromtimestamp(row[0] / 1000)] + row[1:5] for row in response]
    pair_df = pd.DataFrame(data, columns=["time", "open", "high", "low", "close"])
    pair_df['candle_color'] = pair_df.apply(lambda row: 'green' if row.close > row.open else 'red', axis=1)

    # Convert columns to numeric types
    pair_df[["open", "high", "low", "close"]] = pair_df[["open", "high", "low", "close"]].apply(pd.to_numeric)

    return pair_df


def get_mock_pair_data(symbol: str,
                       timeframe: str = "4h",
                       num_candles: int = None,
                       start_time: pd.Timestamp = None) -> pd.DataFrame:
    """
    Fetch the last N historical kline data for a given symbol and return it as a DataFrame.

    Args:
        symbol (str): Trading pair symbol.
        timeframe (str): Timeframe of the candles.
        num_candles (int): Number of candles to fetch from server
        start_time (int): The start UNIX timestamp to start the data from

    Returns:
        pd.DataFrame: DataFrame containing the historical kline data.
    """

    try:
        # Fetch historical kline data
        response = requests.get(f"{constants.mock_api_url}/{symbol}-{timeframe}.hdf5")
        data = json.loads(response.json())
    except Exception as e:
        raise RuntimeError(f"Error fetching historical klines: {e}")

    # Convert UNIX timestamp to UTC time format and create DataFrame
    if num_candles is not None:
        pair_df = pd.DataFrame(data).iloc[-num_candles:].reset_index(drop=True)
        pair_df['time'] = pd.to_datetime(pair_df['time'], unit='ms', utc=True)
    else:
        pair_df = pd.DataFrame(data)
        pair_df['time'] = pd.to_datetime(pair_df['time'], unit='ms', utc=True)
        pair_df = pair_df.loc[pair_df.time >= start_time].reset_index(drop=True)

    # Convert columns to numeric types
    pair_df[["open", "high", "low", "close"]] = pair_df[["open", "high", "low", "close"]].apply(pd.to_numeric)
    pair_df['candle_color'] = pair_df.apply(lambda row: 'green' if row.close > row.open else 'red', axis=1)

    return pair_df


def get_pair_list(pair_list_filename: str = "pair_list.csv") -> list:
    return pd.read_csv(pair_list_filename)["pairs"].tolist()


def get_pair_start_data(pair_name: str) -> dict:
    return {
        "start_time": pd.to_datetime(constants.start_times[pair_name][1:], utc=True),
        "starting_pivot_type": "valley" if constants.start_times[pair_name][0].lower() == "l" else "peak"
    }


def convert_timestamp_to_readable(timestamp: pd.Timestamp):
    utc = timestamp.to_pydatetime()

    def two_char_long(num):
        if num >= 10:
            return str(num)
        else:
            return "0" + str(num)

    readable_format = f"{utc.year}.{utc.month}.{utc.day}/{two_char_long(utc.hour)}:{two_char_long(utc.minute)}:{two_char_long(utc.second)}"

    return readable_format

    # This function finds the higher timeframe necessary to find the starting point


def find_higher_timeframe(lower_timeframe):
    for i, key in enumerate(constants.timeframe_minutes.keys()):
        if key == lower_timeframe:
            return list(constants.timeframe_minutes.keys())[i + constants.higher_timeframe_skip_interval]
