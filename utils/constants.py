from dotenv import dotenv_values
import argparse

# Parse runtime arguments
parser = argparse.ArgumentParser(description="Program configuration")
parser.add_argument("--mode", choices=["dev", "prod"], help="Override the mode from .env.params")
parser.add_argument("--pl", choices=["dev", "prod"], help="Override the mode from .env.params")
args = parser.parse_args()

credentials = dotenv_values("./.env.secret")

params = dotenv_values("./.env.params")

# Override mode if provided as a runtime argument
mode = args.mode if args.mode else credentials["MODE"]

credentials["CHANNEL_ID"] = credentials["CHANNEL_ID"] if credentials["MODE"] == "PROD" else credentials["DEV_CHANNEL_ID"]

validation_mode = True if params["validation_mode"].lower() == "true" else False

if mode.lower() == "dev":
    validation_mode = True

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

leverage = int(params["leverage"])
leverage_type = params["leverage_type"].capitalize()

pair_list_filename = args.pl if args.pl else "pair_list.csv"

# Override the channel ID configuration
channel_id = args.channel_id if args.channel_id else credentials["CHANNEL_ID"]

start_times_filename = f"{timeframe}.env.starttimes"

start_times = dotenv_values(f"./{start_times_filename}")
