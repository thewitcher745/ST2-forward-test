import pandas as pd
import datetime

from algo_code.order_block import OrderBlock
from utils.initialize import initialize, initiate_pair_list
from algo_code.algo import Algo
from algo_code.segment import Segment
from algo_code.position import Position
from algo_code.general_utils import get_pair_data, find_higher_timeframe, get_pairs_start_data, get_pairs_data_parallel
from utils.logger import logger
import utils.constants as constants

pair_list: list[str] = initiate_pair_list()

# This dict contains data indicating the order blocks found and posted for each pair. With each list of positions, a key called
# "latest_segment_start_time" is also saved, which is the time of the latest segment found by the code at the time of that position being added.
# Initially, the position list is empty and the latest segment start time is set to None. In the event of a position being found, this dict is
# populated with appropriate data.
positions_info_dict: dict[str, dict[str, list[Position] | pd.Timestamp | None]] = {}

for pair_name in pair_list:
    positions_info_dict[pair_name] = {}
    positions_info_dict[pair_name]["positions"] = []
    positions_info_dict[pair_name]["latest_segment_start_time"] = None

#  Initializing the starting data
pairs_start_data = get_pairs_start_data(pair_list)
pairs_start_times = {pair_name: pairs_start_data[pair_name]["start_time"] for pair_name in pairs_start_data.keys()}
paits_starting_pivot_types = {pair_name: pairs_start_data[pair_name]["starting_pivot_type"] for pair_name in pairs_start_data.keys()}

while True:
    # Get the data for all the pairs in parallel. Data for each pair is stored as the value and as a pd.DataFrame.
    try:
        pairs_data: dict[str, pd.DataFrame] = get_pairs_data_parallel(pair_list, pairs_start_times)
    except Exception as e:
        logger.warning(f"Error fetching data for pairs: {e}... skipping an iteration...")
        continue

    for pair_name in pair_list:
        start_data = pairs_start_data[pair_name]
        start_time: pd.Timestamp = pairs_start_times[pair_name]
        starting_pivot_type: str = paits_starting_pivot_types[pair_name]

        pair_df: pd.DataFrame = pairs_data[pair_name]

        latest_candle = pair_df.iloc[-1]

        algo = Algo(pair_df=pair_df, symbol=pair_name, timeframe=constants.timeframe)
        algo.init_zigzag(last_pivot_type=starting_pivot_type, last_pivot_candle_pdi=0)

        try:
            h_o_starting_point: int = int(algo.zigzag_df.iloc[0].pdi)
        except:
            logger.warning(
                f"\t{pair_name}\tThe starting point entered isn't a lower order zigzag pivot... Consider changing the starting point. "
                f"Skipping the pair...")
            continue

        # try:
        algo.calc_h_o_zigzag(starting_point_pdi=h_o_starting_point)
        # except Exception as e:
        #     logger.warning(f"\t{pair_name}\tError calculating HO zigzag: {e}")
        #     continue

        # The last segment found by the code
        latest_segment: Segment = algo.segments[-1]

        # If the latest segment's start time is newer than the start time of the segment registered when the positions were found (Or if we are starting
        # fresh with no latest_segment registered), that means the old segment has been invalidated by a new segment forming.
        # In this case, the existing positions (if any) should be canceled and new ones should be posted or awaited.
        is_starting_fresh: bool = positions_info_dict[pair_name]["latest_segment_start_time"] is None
        is_new_segment_found: bool = is_starting_fresh or algo.convert_pdis_to_times(latest_segment.start_pdi) > positions_info_dict[pair_name][
            "latest_segment_start_time"]

        # If we are not in a new segment, and we aren't starting with no positions, we can skip the rest of the code for this pair.
        if not is_new_segment_found and not is_starting_fresh:
            logger.debug(f"\t{pair_name}\tNo new segment found, no updates made.")
            continue

        # If there is a new segment, the rest of the code will execute, but also the positions found in the previous segment will be canceled.
        else:
            if is_starting_fresh:
                logger.info(f"\t{pair_name}\tNo Prior latest segment history, starting fresh...")

            elif is_new_segment_found:
                logger.info(f"\t{pair_name}\tNew segment found, canceling prior positions...")

            for position in positions_info_dict[pair_name]["positions"]:
                position.cancel_position()

            # Empty the list of positions, so we can wait for a new one.
            positions_info_dict[pair_name]["positions"] = []

            # Regardless o whether any positions are found or not in the future lines, we need to register the latest segment.
            positions_info_dict[pair_name]["latest_segment_start_time"] = algo.convert_pdis_to_times(latest_segment.start_pdi)

            logger.debug(f"\t{pair_name}\tLatest segment start time registered: {positions_info_dict[pair_name]['latest_segment_start_time']}")

        # If the latest segment is finished (Which it should have, since segments only register once the end condition is met), find the leg which the
        # positions should form on.
        latest_segment_end_time: pd.Timestamp = pair_df.iloc[latest_segment.end_pdi].time

        if latest_candle.time >= latest_segment_end_time:
            position_search_window = algo.find_position_search_window(latest_segment)

            # If no broken LPL is found, the method returns None; So we would move on to the next pair.
            if position_search_window is None:
                continue

            position_search_start_pdi = position_search_window["start"]
            position_search_end_pdi = position_search_window["end"]
            position_activation_threshold = position_search_window["activation_threshold"]

            base_pivot_type = "valley" if latest_segment.type == "ascending" else "peak"

            # Positions should only be posted once the activation threshold has passed. This condition would normally implicitly pass, but for the
            # sake of clarity, it is explicitly stated.
            if latest_candle.time > algo.pair_df.iloc[position_activation_threshold].time:
                # Iterate through pivots of the correct type, located in the correct range. Same logic as finding order blocks in segments.
                eligible_lo_pivots = algo.zigzag_df[(algo.zigzag_df.pivot_type == base_pivot_type) &
                                                    (position_search_start_pdi <= algo.zigzag_df.pdi) &
                                                    (algo.zigzag_df.pdi < position_search_end_pdi)]
                for pivot in eligible_lo_pivots.itertuples():
                    # Form a window of candles to check for replacement order blocks. This window is bound by the current pivot and the next pivot of
                    # opposite type, hence the pivot and the pivot found by shifting it by 1. This is a naive implementation, and under normal
                    # circumstances we don't need to check that far.
                    try:
                        next_pivot_pdi = algo.find_relative_pivot(pivot.pdi, 1)
                        replacement_ob_threshold_pdi = next_pivot_pdi
                    except IndexError:
                        # If no next pivot exists for whatever reason, just set the threshold to the last valid index of the dataframe.
                        replacement_ob_threshold_pdi = algo.pair_df.last_valid_index()

                    # This variable is used to calculate the initial liquidity of the order block. It is the liquidity of the pivot candle on the
                    # "tip" of the LO zigzag. The value is used for setting the stoploss for the positions.
                    initial_pivot_candle_liquidity: float = pivot.pivot_value

                    # Iterate through the candle in the LO zigzag leg, trying to find the first base candle that forms a valid order block.
                    for base_candle_pdi in range(pivot.pdi, replacement_ob_threshold_pdi):
                        base_candle = algo.pair_df.iloc[base_candle_pdi]
                        ob = OrderBlock(base_candle=base_candle,
                                        icl=initial_pivot_candle_liquidity,
                                        ob_type="long" if base_pivot_type == "valley" else "short")

                        # Try to find a valid exit candle for the order block.
                        ob.register_exit_candle(algo.pair_df, position_activation_threshold)

                        # If a valid exit candle is found, form the reentry check window.
                        if ob.price_exit_index is not None:
                            reentry_check_window: pd.DataFrame = algo.pair_df.iloc[ob.price_exit_index + 1:position_activation_threshold]

                        # If no exit candle is found, that means that order block isn't valid, and the search for a valid OB must continue with
                        # the next candle.
                        else:
                            continue

                        # Order block condition checks
                        ob.check_reentry_condition(reentry_check_window)

                        conditions_check_window: pd.DataFrame = algo.pair_df[ob.start_index:position_activation_threshold]
                        ob.set_condition_check_window(conditions_check_window)
                        ob.check_fvg_condition()
                        ob.check_stop_break_condition()

                        # If a valid order block which passes all the checks and conditions is found, post it to the channel and add it to the list of
                        # positions found for this pair.
                        if ob.has_reentry_condition and ob.has_fvg_condition and ob.has_stop_break_condition:
                            # Validation data to be appended to the signal
                            validation_data = {
                                "activation_time": algo.pair_df.iloc[position_activation_threshold].time,
                                "broken_lpl": algo.pair_df.iloc[position_search_end_pdi].time,
                            }
                            ob.position.message_id = ob.position.post_to_channel(pair_name, validation_data)

                            # Add the found position to the list of positions for this pair, and set the latest segment start time to the time of the
                            # latest segment's start time at the time of finding the positions.
                            positions_info_dict[pair_name]["positions"].append(ob.position)
                            logger.info(f"\t{pair_name}\tPosition found, OBID {ob.id}")

                            break
