# -*- coding: utf-8 -*-

import sys
from src.criterias.interfaces import *

class DecreasingChip1(ICriteria):
    def check(self, data_sets):
        #print(data_sets)
        last_data_set = data_sets[-1]

        # 季乖離率超過 20%
        bias = ((last_data_set['closing_price'] / last_data_set['ma_60']) - 1) * 100
        if bias < 20:
            return False

        # 20 日集中度開始下降

        # 主力開始賣超
        return True


class StopDecreasingChip1(ICriteria):
    def check(self, data_sets):
        pass
