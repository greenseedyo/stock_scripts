# -*- coding: utf-8 -*-

import sys
from src.criterias.interfaces import *

class DecreasingChip1(ICriteria):
    def check(self, data_sets):
        print(data_sets)
        # 季乖離率超過 20%

        # 20 日集中度開始下降

        # 主力開始賣超
        pass
