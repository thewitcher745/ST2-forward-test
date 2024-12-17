import pandas as pd
import datetime

from algo_code.order_block import OrderBlock
from utils.initialize import initialize, initiate_pair_list
from algo_code.algo import Algo
from algo_code.segment import Segment
from algo_code.position import Position
from algo_code.general_utils import get_pair_data, find_higher_timeframe, get_pair_start_data
import utils.constants as constants

pair_list: list[str] = initiate_pair_list()
# initialize()

# higher_timeframe = find_higher_timeframe(constants.timeframe)

for pair_name in pair_list:
    # logger.info(f"Processing pair: {pair_name}")
    start_data = get_pair_start_data(pair_name)
    start_time: pd.Timestamp = start_data["start_time"]
    starting_pivot_type: str = start_data["starting_pivot_type"]

    pair_df: pd.DataFrame = get_pair_data(pair_name, start_time)
    latest_candle = pair_df.iloc[-1]

    algo = Algo(pair_df=pair_df, symbol=pair_name, timeframe=constants.timeframe)
    algo.init_zigzag(last_pivot_type=starting_pivot_type, last_pivot_candle_pdi=0)
    try:
        h_o_starting_point: int = int(algo.zigzag_df.iloc[0].pdi)
    except:
        continue

    algo.calc_h_o_zigzag(starting_point_pdi=h_o_starting_point)

    # print(algo.segments)

    # The last segment found by the code
    latest_segment: Segment = algo.segments[-1]
    # print([pair_df.iloc[h_o_index].time for h_o_index in algo.h_o_indices[-5:]])

    # print(latest_segment.formation_method, latest_segment.type)
    # print(pair_df.iloc[latest_segment.start_pdi].time,
    #       pair_df.iloc[latest_segment.end_pdi].time,
    #       pair_df.iloc[latest_segment.ob_formation_start_pdi].time,
    #       pair_df.iloc[latest_segment.broken_lpl_pdi].time)

    # If the latest segment is finished (Which it should have, since segments only register once the end condition is met), find the leg which the
    # positions should form on.
    if pair_df.iloc[-1].time >= pair_df.iloc[latest_segment.end_pdi].time:
        # If the latest segment was formed from a BOS break, that means the direction hasn't changed. So the latest found leg (of the same direction)
        # is still valid. The start of the position search would be the second-to-last higher order zigzag pivot, and the end of it would be the LPL
        # that is broken.
        if latest_segment.formation_method == "bos":
            position_search_start_pdi: int = algo.h_o_indices[-2]

            # The detect_first_broken_lpl method returns two things as a tuple: 1) The LPL that was broken 2) The PDI of the candle that broke the
            # LPL. We need the first element of the tuple here.
            # The end of the search window is set as the first broken LPL AFTER the end of the last segment. This is the same logic used in the
            # finding of the HO indices.
            pivot_type = "valley" if latest_segment.type == "ascending" else "peak"
            pivots_of_type_before_closing_candle = algo.zigzag_df[(algo.zigzag_df.pivot_type == pivot_type)
                                                                  & (algo.zigzag_df.pdi <= latest_segment.end_pdi)]
            broken_lpl_data = algo.detect_first_broken_lpl(pivots_of_type_before_closing_candle.iloc[-1].pdi)
            if broken_lpl_data:
                position_search_end_pdi: int = broken_lpl_data[0].pdi

                # The positions should only be activated after the LPL has been broken by a candle.
                position_activation_threshold: int = broken_lpl_data[1]

            else:
                continue

        else:
            position_search_start_pdi: int = algo.h_o_indices[-1]

            # The detect_first_broken_lpl method returns two things as a tuple: 1) The LPL that was broken 2) The PDI of the candle that broke the
            # LPL. We need the first element of the tuple here.
            # The end of the search window is set as the first broken LPL AFTER the end of the last segment. This is the same logic used in the
            # finding of the HO indices.
            pivot_type = "peak" if latest_segment.type == "ascending" else "valley"
            pivots_of_type_before_closing_candle = algo.zigzag_df[(algo.zigzag_df.pivot_type == pivot_type)
                                                                  & (algo.zigzag_df.pdi <= latest_segment.end_pdi)]
            broken_lpl_data = algo.detect_first_broken_lpl(pivots_of_type_before_closing_candle.iloc[-1].pdi)
            if broken_lpl_data:
                position_search_end_pdi: int = broken_lpl_data[0].pdi

                # The positions should only be activated after the LPL has been broken by a candle.
                position_activation_threshold: int = broken_lpl_data[1]

            else:
                continue

        # print("Position search starts at: ", algo.convert_pdis_to_times(position_search_start_pdi))
        # print("Position search ends at: ", algo.convert_pdis_to_times(position_search_end_pdi))
        # print("Position activation threshold: ", algo.convert_pdis_to_times(position_activation_threshold))

        base_pivot_type = "valley" if latest_segment.type == "ascending" else "peak"

        if latest_candle.time > algo.pair_df.iloc[position_activation_threshold].time:
            # Iterate through pivots of the correct type, located in the correct range. Same logic as finding order blocks in segments.
            for pivot in algo.zigzag_df[(algo.zigzag_df.pivot_type == base_pivot_type) &
                                        (position_search_start_pdi <= algo.zigzag_df.pdi) &
                                        (algo.zigzag_df.pdi < position_search_end_pdi)].itertuples():
                try:
                    next_pivot_pdi = algo.find_relative_pivot(pivot.pdi, 1)
                    replacement_ob_threshold_pdi = next_pivot_pdi
                except IndexError:
                    replacement_ob_threshold_pdi = algo.pair_df.last_valid_index()

                initial_pivot_candle_liquidity = pivot.pivot_value

                for base_candle_pdi in range(pivot.pdi, replacement_ob_threshold_pdi):
                    base_candle = algo.pair_df.iloc[base_candle_pdi]
                    ob = OrderBlock(base_candle=base_candle,
                                    icl=initial_pivot_candle_liquidity,
                                    ob_type="long" if base_pivot_type == "valley" else "short")

                    ob.register_exit_candle(algo.pair_df, position_activation_threshold)

                    if ob.price_exit_index is not None:
                        reentry_check_window: pd.DataFrame = algo.pair_df.iloc[ob.price_exit_index + 1:position_activation_threshold]

                    else:
                        continue

                    ob.check_reentry_condition(reentry_check_window)

                    conditions_check_window: pd.DataFrame = algo.pair_df[ob.start_index:position_activation_threshold]
                    ob.set_condition_check_window(conditions_check_window)

                    ob.check_fvg_condition()
                    ob.check_stop_break_condition()

                    if ob.has_reentry_condition and ob.has_fvg_condition and ob.has_stop_break_condition:
                        validation_data = {
                            "activation_time": algo.pair_df.iloc[position_activation_threshold].time,
                            "broken_lpl": algo.pair_df.iloc[broken_lpl_data[0].pdi].time,
                        }

                        ob.position.post_to_channel(pair_name, validation_data)
                        # print(ob)
                        # print("Broken LPL", algo.convert_pdis_to_times(broken_lpl_data[0].pdi))
                        # print("Position activation at", algo.convert_pdis_to_times(position_activation_threshold))
                        # print(ob.position.compose_signal_message(pair_name))
                        break
