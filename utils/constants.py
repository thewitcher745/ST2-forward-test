from dotenv import dotenv_values

credentials = dotenv_values("./.env.secret")
params = dotenv_values("./.env.params")
start_times = dotenv_values("./.env.starttimes")

mode = credentials["MODE"]
validation_mode = True if params["validation_mode"].lower() == "true" else False
market_type = params["market_type"]
main_loop_interval = int(params["main_loop_interval"])
price_rounding_precision = int(params["price_rounding_precision"])

# The lower order timeframe
timeframe = params['timeframe']

# The skip "interval" between the low and high timeframe, 2 means that the low timeframe is 2 times smaller than the high timeframe,
# as in 15m becomes 4h, 1h becomes 1d, etc.
higher_timeframe_skip_interval = 2

# The timeframe values in minutes, used for conversion
timeframe_minutes = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "1h": 60,
    "4h": 240,
    "1d": 1440
}

mock_api_url = credentials["MOCK_API_URL"]

num_pairs_engaged = params["num_pairs_engaged"]

stoploss_coeff: float = float(params["stoploss_coeff"])