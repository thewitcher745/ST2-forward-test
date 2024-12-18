import datetime
import time
import requests
import pandas as pd
import json

from utils import constants

import concurrent.futures


def get_pairs_data_parallel(symbols: list, start_times: dict) -> dict:
    """
    Fetch the last N historical kline data for given symbols and return it as a dictionary of DataFrames.

    Args:
        symbols (list): List of trading pair symbols.
        start_times (dict): Dictionary containing start_time of the candles for each symbol.

    Returns:
        dict: Dictionary containing the historical kline data for each symbol.
    """

    def fetch_data_for_symbol(symbol) -> pd.DataFrame | None:
        # Convert start_time to milliseconds
        start_time = start_times[symbol]
        start_time_ms = int(start_time.timestamp() * 1000)
        end_time_ms = int(time.time() * 1000)  # Current time in milliseconds
        timeframe_seconds = pd.Timedelta(constants.timeframe).total_seconds()
        max_candles = 1000

        if constants.market_type == "futures":
            url = f"https://fapi.binance.com/fapi/v1/klines"
        elif constants.market_type == "spot":
            url = f"https://api.binance.com/api/v3/klines"

        all_data = []
        current_start_time_ms = start_time_ms

        while current_start_time_ms < end_time_ms:
            params = {
                "symbol": symbol,
                "interval": constants.timeframe,
                "startTime": current_start_time_ms,
                "endTime": end_time_ms,
                "limit": max_candles
            }

            try:
                # Fetch historical kline data
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                if not data:
                    break
                all_data.extend(data)
                current_start_time_ms = data[-1][0] + 1  # Move to the next timestamp after the last one fetched
            except Exception as e:
                return None

        # Convert UNIX timestamp to UTC time format and create DataFrame
        data = [[datetime.datetime.utcfromtimestamp(row[0] / 1000)] + row[1:5] for row in all_data]
        pair_df = pd.DataFrame(data, columns=["time", "open", "high", "low", "close"])
        pair_df['candle_color'] = pair_df.apply(lambda row: 'green' if row.close > row.open else 'red', axis=1)

        # Convert columns to numeric types
        pair_df[["open", "high", "low", "close"]] = pair_df[["open", "high", "low", "close"]].apply(pd.to_numeric)

        return symbol, pair_df

    all_pairs_data = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(fetch_data_for_symbol, symbol): symbol for symbol in symbols}
        for future in concurrent.futures.as_completed(futures):
            symbol, pair_df = future.result()
            all_pairs_data[symbol] = pair_df

    return all_pairs_data


def get_pair_data(symbol: str, start_time: pd.Timestamp) -> pd.DataFrame | None:
    """
    Fetch the last N historical kline data for a given symbol and return it as a DataFrame.

    Args:
        symbol (str): Trading pair symbol.
        start_time (pd.Timestamp): start_time of the candles

    Returns:
        pd.DataFrame: DataFrame containing the historical kline data.
    """

    # Convert start_time to milliseconds
    start_time_ms = int(start_time.timestamp() * 1000)
    end_time_ms = int(time.time() * 1000)  # Current time in milliseconds
    timeframe_seconds = pd.Timedelta(constants.timeframe).total_seconds()
    max_candles = 1000

    if constants.market_type == "futures":
        url = f"https://fapi.binance.com/fapi/v1/klines"
    elif constants.market_type == "spot":
        url = f"https://api.binance.com/api/v3/klines"

    all_data = []

    while start_time_ms < end_time_ms:
        params = {
            "symbol": symbol,
            "interval": constants.timeframe,
            "startTime": start_time_ms,
            "endTime": end_time_ms,
            "limit": max_candles
        }

        try:
            # Fetch historical kline data
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if not data:
                break
            all_data.extend(data)
            start_time_ms = data[-1][0] + 1  # Move to the next timestamp after the last one fetched
        except Exception as e:
            return None

    # Convert UNIX timestamp to UTC time format and create DataFrame
    data = [[datetime.datetime.utcfromtimestamp(row[0] / 1000)] + row[1:5] for row in all_data]
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


def get_pairs_start_data(pair_list: list[str]) -> dict:
    # Get the start data for a list of pairs. Returns a dict containing the start time and starting pivot type for each pair.
    return {pair: get_pair_start_data(pair) for pair in pair_list}


def get_pair_start_data(pair_name: str) -> dict:
    # Get the start data for a single pair. Returns a dict containing the start time and the starting pivot type for that pair, manually provided.
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


def make_set_width(string):
    return string.ljust(12)
