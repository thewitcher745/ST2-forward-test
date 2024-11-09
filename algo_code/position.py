from typing import Union
import pandas as pd


class Position:
    def __init__(self, stoploss: float, parent_ob):
        # Entries, targets and stoploss
        self.parent_ob = parent_ob
        self.entry_price = parent_ob.top if parent_ob.type == "long" else parent_ob.bottom
        self.stoploss = stoploss
        self.position_height = abs(self.entry_price - self.stoploss)
        self.type = parent_ob.type

        self.status: str = "ACTIVE"
        self.entry_pdi = None
        self.qty: float = 0
        self.highest_target: int = 0
        self.target_hit_pdis: list[int] = []
        self.exit_pdi = None
        self.portioned_qty = []
        self.net_profit = None

        if self.type == "long":
            self.target_list = [
                self.entry_price + 3 * self.position_height,
                self.entry_price + 5 * self.position_height,
                self.entry_price + 7 * self.position_height,
            ]
        else:
            self.target_list = [
                self.entry_price - 3 * self.position_height,
                self.entry_price - 5 * self.position_height,
                self.entry_price - 7 * self.position_height,
            ]
