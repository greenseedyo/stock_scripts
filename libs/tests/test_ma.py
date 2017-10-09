# -*- coding: utf-8 -*-

from .context import *
import datetime

from src.ma import MA

class TestMA(unittest.TestCase):
    def test_calculate(self):
        stock_code = '0050'
        date_obj = datetime.datetime.strptime('2017-09-01', "%Y-%m-%d")
        ma = MA().calculate(stock_code, date_obj, 5)
        self.assertEqual(ma, 82.7)
