# Cancels all the pairs in pair_list.csv

from utils.channel_utils import post_message
import utils.constants as constants

confirmation_input = input("About to cancel all signals in the list above. Continue (Y/N)?")

if confirmation_input.lower() == "y":
    for symbol in open(constants.pair_list_filename):
        if "pairs" not in symbol:
            separated_symbol = symbol.replace("US", "/US")
            post_message(f"Cancel #{separated_symbol}")
