import pandas as pd
import datetime
from utils.initialize import initialize, initiate_pair_list
from algo_code.algo import Algo
from algo_code.general_utils import get_mock_pair_data, find_higher_timeframe, get_pair_start_data
import utils.constants as constants

pair_list: list[str] = initiate_pair_list()
# initialize()

# higher_timeframe = find_higher_timeframe(constants.timeframe)

for pair_name in pair_list:
    # logger.info(f"Processing pair: {pair_name}")
    start_data = get_pair_start_data(pair_name)
    start_time: pd.Timestamp = start_data["start_time"]
    starting_pivot_type: str = start_data["starting_pivot_type"]

    pair_df: pd.DataFrame = get_mock_pair_data(pair_name, constants.timeframe, start_time=start_time)

    algo = Algo(pair_df=pair_df, symbol=pair_name, timeframe=constants.timeframe)
    algo.init_zigzag(last_pivot_type=starting_pivot_type, last_pivot_candle_pdi=0)
    h_o_starting_point: int = int(algo.zigzag_df.iloc[0].pdi)
    algo.calc_h_o_zigzag(starting_point_pdi=h_o_starting_point)
