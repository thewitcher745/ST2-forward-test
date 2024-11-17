from typing import Union
import pandas as pd

import algo_code.position_prices_setup as setup

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

