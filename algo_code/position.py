from utils.channel_utils import post_message
import algo_code.position_prices_setup as setup
import utils.constants as constants


class Position:
    def __init__(self, parent_ob):
        self.parent_ob = parent_ob
        self.entry_price = parent_ob.top if parent_ob.type == "long" else parent_ob.bottom

        # Calculation of stoploss is done using the distance from the entry of the box to the initial candle that was checked for OB, before being
        # potentially replaced. This distance is denoted as EDICL, entry distance from initial candle liquidity.
        self.edicl = abs(parent_ob.icl - self.entry_price)

        self.type = parent_ob.type

        self.status: str = "ACTIVE"
        self.entry_pdi = None
        self.qty: float = 0
        self.highest_target: int = 0
        self.target_hit_pdis: list[int] = []
        self.exit_pdi = None
        self.portioned_qty = []
        self.net_profit = None

        self.target_list = []
        self.stoploss = None

        # Set up the target list nd stoploss using a function which operates on the "self" object and directly manipulates the instance.
        setup.default_357(self)

        # This variable will be assigned a value once the position is posted to the channel. The value will be used to cancel it once the segment
        # containing the position expires.
        self.message_id = None

    def compose_signal_message(self, symbol, validation_data: dict):
        symbol_for_signal = symbol.replace("US", "/US")
        message = f"""⚡️⚡️ #{symbol_for_signal} ⚡️⚡️
Exchanges: Binance Futures
Signal Type: Regular ({self.type})
Leverage: {constants.leverage_type} ({constants.leverage}.0X)

Entry Targets:
"""

        message += f"1) {float(round(self.entry_price, constants.price_rounding_precision))}\n"

        message += "\nTake-Profit Targets: \n"

        for target_id, target in enumerate(self.target_list):
            message += f"{target_id + 1}) {round(target, constants.price_rounding_precision)} \n"

        message += "\nStop Targets: \n"
        message += f"1) {round(self.stoploss, constants.price_rounding_precision)}\n"

        if constants.validation_mode:
            message += f"\nBase candle:\n{self.parent_ob.base_candle}\n"
            message += f"\nSignal activation time: \n{validation_data['activation_time']}\n"
            message += f"\nBroken LPL time: \n{validation_data['broken_lpl']}\n"
            message += f"\nSearch window: \n{validation_data['position_search_window'][0]} to {validation_data['position_search_window'][1]}\n"
            message += f"\nLatest segment: \n{validation_data['latest_segment_bounds'][0]} to {validation_data['latest_segment_bounds'][1]}\n"
            message += f"\nLatest segment HO pivots: \n{validation_data['latest_segment_ho_pivots']}\n"

        return message

    def post_to_channel(self, symbol, validation_data: dict):
        message = self.compose_signal_message(symbol, validation_data)
        return post_message(message)

    def cancel_position(self):
        post_message("Cancel", self.message_id)
