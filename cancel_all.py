# Cancels all the pairs in pair_list.csv

from utils.channel_utils import post_message

for symbol in open("pair_list.csv"):
    if "pairs" not in symbol:
        separated_symbol = symbol.replace("US", "/US")
        post_message(f"Cancel #{separated_symbol}")
