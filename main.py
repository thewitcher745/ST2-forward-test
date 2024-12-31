import pandas as pd
import time

from utils.initialize import initiate_pair_list
from algo_code.algo import Algo
from algo_code.segment import Segment
from algo_code.position import Position
from algo_code.general_utils import get_pairs_start_data, get_pairs_data_parallel, make_set_width
from utils.logger import logger
import utils.constants as constants

pair_list: list[str] = initiate_pair_list()

# This dict contains data indicating the order blocks found and posted for each pair. With each list of positions, a key called
# "latest_segment_start_time" is also saved, which is the time of the latest segment found by the code at the time of that position being added.
# Initially, the position list is empty and the latest segment start time is set to None. In the event of a position being found, this dict is
# populated with appropriate data.
# Added is the "has_been_searched" key, which is used to determine if an appropriate HO zigzag leg has been searched for positions. If True, the
# algorithm waits until the next segment is found before searching for positions again.
positions_info_dict: dict[str, dict[str, list[Position] | pd.Timestamp | None | bool]] = {}

for pair_name in pair_list:
    positions_info_dict[pair_name] = {}
    positions_info_dict[pair_name]["positions"] = []
    positions_info_dict[pair_name]["latest_segment_start_time"] = None
    positions_info_dict[pair_name]["has_been_searched"] = None

#  Initializing the starting data
pairs_start_times, pairs_starting_pivot_types = get_pairs_start_data(pair_list)

while True:
    # Get the data for all the pairs in parallel. Data for each pair is stored as the value and as a pd.DataFrame. Error handling is done per-pair
    # further down.
    pairs_data: dict[str, pd.DataFrame] = get_pairs_data_parallel(pair_list, pairs_start_times)

    for pair_name in pair_list:
        start_time: pd.Timestamp = pairs_start_times[pair_name]
        starting_pivot_type: str = pairs_starting_pivot_types[pair_name]

        pair_df: pd.DataFrame = pairs_data[pair_name]

        # If the API fails to respond, instead of the dataframe in the API response there will be None. If this happens, the algo moves on to the next
        # pair in the list and tries the failed pair again in the next iteration.
        if pair_df is None:
            logger.warning(f"\t{make_set_width(pair_name)}\tNo data for pair found. The fetching most likely failed. Skipping...")
            continue

        latest_candle = pair_df.iloc[-1]

        # HO zigzag calculations __________________________________________________________________
        algo = Algo(pair_df=pair_df, symbol=pair_name)
        algo.init_zigzag(last_pivot_type=starting_pivot_type, last_pivot_candle_pdi=0)
        try:
            h_o_starting_point: int = int(algo.zigzag_df.iloc[0].pdi)
        except:
            logger.warning(
                f"\t{make_set_width(pair_name)}\tThe starting point entered isn't a lower order zigzag pivot... Consider changing the starting point."
                f" Skipping the pair...")
            continue
        algo.calc_h_o_zigzag(starting_point_pdi=h_o_starting_point)

        # Determining where in the pattern we are _________________________________________________
        try:
            # The last segment found by the code
            latest_segment: Segment = algo.segments[-1]
        except IndexError:
            logger.debug(f"\t{make_set_width(pair_name)}\tNo segments found, skipping the pair...")
            continue

        start_type = algo.determine_main_loop_start_type(pair_name, positions_info_dict)
        # If we are still in the same segment, don't do anything. Go to the next pair.
        if start_type == "NO_NEW_SEGMENT":
            # If we have already searched for positions in the current segment, we don't need to search again. We can move on to the next pair.
            if positions_info_dict[pair_name]["has_been_searched"]:
                # logger.debug(f"\t{make_set_width(pair_name)}\tThe positions for the most recent appropriate HO leg have been processed, waiting...")
                continue

            # Otherwise, if the latest segment has a BOS formation type, and after it has ended the new HO zigzag point has not yet formed, that means
            # the segment has ended by a candle closing above/below the BOS, but no appropriate HO zigzag leg exists to search for positions.
            elif latest_segment.formation_method == "bos" and latest_candle.time >= algo.convert_pdis_to_times(latest_segment.end_pdi) and len(
                    [h_o_pivot_pdi for h_o_pivot_pdi in algo.h_o_indices if h_o_pivot_pdi > latest_segment.end_pdi]) == 0:
                # logger.debug(f"\t{make_set_width(pair_name)}\tNo new HO zigzag leg found after the last segment, waiting...")
                continue

            logger.debug(f"\t{make_set_width(pair_name)}\tPosition searching is required...")

            # If none of the "waiting" conditions are true, that means the positions should be getting searched for and posted, if any are found valid

        # Position formation ______________________________________________________________________
        # If the latest segment is finished (Which it should have, since segments only register once the end condition is met), find the leg which the
        # positions should form on.
        latest_segment_end_time: pd.Timestamp = pair_df.iloc[latest_segment.end_pdi].time

        if latest_candle.time >= latest_segment_end_time:
            position_search_window = algo.find_position_search_window(latest_segment)

            # If no broken LPL is found, the method returns None; So we would move on to the next pair.
            if position_search_window is None:
                continue
            else:
                position_search_start_pdi = position_search_window["start"]
                position_search_end_pdi = position_search_window["end"]
                position_activation_threshold = position_search_window["activation_threshold"]

                positions_info_dict[pair_name]["has_been_searched"] = True
                logger.debug(
                    f"\t{make_set_width(pair_name)}\tSearching for positions in the window "
                    f"{algo.convert_pdis_to_times([position_search_start_pdi, position_search_end_pdi])}...")

            base_pivot_type = "valley" if latest_segment.type == "ascending" else "peak"

            # Finding eligible pivots for position formation ______________________________________
            # Positions should only be posted once the activation threshold has passed. This condition would normally implicitly pass, but for the
            # sake of clarity, it is explicitly stated.
            if latest_candle.time > algo.pair_df.iloc[position_activation_threshold].time:
                # Iterate through pivots of the correct type, located in the correct range. Same logic as finding order blocks in segments.
                eligible_lo_pivots = algo.zigzag_df[(algo.zigzag_df.pivot_type == base_pivot_type) &
                                                    (position_search_start_pdi <= algo.zigzag_df.pdi) &
                                                    (algo.zigzag_df.pdi < position_search_end_pdi)]

                # Finding a good base candle ______________________________________________________
                for pivot in eligible_lo_pivots.itertuples():
                    # The PDI of the last candle that needs to be checked to find a replacement.
                    replacement_ob_threshold_pdi = algo.define_replacement_ob_threshold(pivot)

                    # This variable is used to calculate the initial liquidity of the order block. It is the liquidity of the pivot candle on the
                    # "tip" of the LO zigzag. The value is used for setting the stoploss for the positions.
                    initial_pivot_candle_liquidity: float = pivot.pivot_value

                    # Iterate through the candle in the LO zigzag leg, trying to find the first base candle that forms a valid order block.
                    for base_candle_pdi in range(pivot.pdi, replacement_ob_threshold_pdi):
                        base_candle = algo.pair_df.iloc[base_candle_pdi]
                        ob = algo.form_potential_ob(base_candle, base_pivot_type, initial_pivot_candle_liquidity, position_activation_threshold)

                        # If no OB has been found (typically due to no exit candle being found), move on to the next candle in the replacement window.
                        if ob is None:
                            continue

                        # Registering and posting a discovered OB _________________________________
                        # If a valid order block which passes all the checks and conditions is found, post it to the channel and add it to the list of
                        # positions found for this pair.
                        if ob.has_reentry_condition and ob.has_fvg_condition and ob.has_stop_break_condition:
                            # Validation data to be appended to the signal
                            validation_data = {
                                "activation_time": algo.pair_df.iloc[position_activation_threshold].time,
                                "broken_lpl": algo.pair_df.iloc[position_search_end_pdi].time,
                                "position_search_window": algo.convert_pdis_to_times([position_search_start_pdi, position_search_end_pdi]),
                                "latest_segment_bounds": algo.convert_pdis_to_times([latest_segment.start_pdi, latest_segment.end_pdi]),
                                "latest_segment_ho_pivots": algo.convert_pdis_to_times(
                                    [index for index in algo.h_o_indices if latest_segment.start_pdi <= index])
                            }
                            ob.position.message_id = ob.position.post_to_channel(pair_name, validation_data)

                            # Add the found position to the list of positions for this pair, and set the latest segment start time to the time of the
                            # latest segment's start time at the time of finding the positions.
                            positions_info_dict[pair_name]["positions"].append(ob.position)
                            logger.info(f"\t{make_set_width(pair_name)}\tPosition found, OBID {ob.id}")

                            # If a position is found, we don't need to keep looking for valid OB's. We can break out of the loop and move on to the
                            # next "tip" pivot in the search window.
                            break

    time.sleep(constants.main_loop_interval)
