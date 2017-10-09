# -*- coding: utf-8 -*-

from .context import *

import datetime

from src.chip import *
from src.inventory import *
from src.rule import *
from src.criterias.short import *

class TestChip(unittest.TestCase):
    def setUp(self):
        self.chip = Chip()

    def tearDown(self):
        self.chip = None

    def _set_test_rule(self):
        rule = Rule()

        buying_criteria = DecreasingChip1()
        rule.set_buying_criteria(buying_criteria)

        buying_more_criteria = DecreasingChip1()
        rule.set_buying_more_criteria(buying_more_criteria)

        selling_criteria = DecreasingChip1()
        rule.set_selling_criteria(selling_criteria)

        self.chip.set_rule(rule)

    def test_get_raw_data(self):
        # 檔案存在
        stock_code = '0050'
        period = '1day'
        date_obj = datetime.datetime.strptime('2017-09-07', "%Y-%m-%d")
        raw_data = self.chip._get_raw_data(stock_code, period, date_obj)
        self.assertEqual(9316, len(raw_data))
        # 檔案不存在
        stock_code = '9999'
        period = 'abc'
        date_obj = datetime.datetime.strptime('2017-09-07', "%Y-%m-%d")
        with self.assertRaises(FileNotFoundError):
            raw_data = self.chip._get_raw_data(stock_code, period, date_obj)

    def test_get_force_net_by_raw_data(self):
        stock_code = '0050'
        period = '1day'
        date_obj = datetime.datetime.strptime('2017-09-01', "%Y-%m-%d")
        raw_data = self.chip._get_raw_data(stock_code, period, date_obj)
        force_net = self.chip._get_major_force_net(raw_data)
        self.assertEqual(force_net, 757)

    def test_get_volume(self):
        stock_code = '0050'
        date_obj = datetime.datetime.strptime('2017-09-01', "%Y-%m-%d")
        days_period = 5
        volume = self.chip._get_volume(stock_code, date_obj, days_period)
        self.assertEqual(volume, 15835525)

    def test_get_one_day_data(self):
        stock_code = '0050'
        date_obj = datetime.datetime.strptime('2017-09-01', "%Y-%m-%d")
        data = self.chip._get_one_day_data(stock_code, date_obj)
        self.assertEqual(data['major_force_net'], 757)
        self.assertEqual(data['concentration_5days'], 27.91)
        self.assertEqual(data['concentration_20days'], 2.05)

    def test_simulate_one(self):
        stock_code = '1313'
        date_obj = datetime.datetime.strptime('2017-06-01', "%Y-%m-%d")
        self._set_test_rule()
        data = self.chip.simulate_one(stock_code, date_obj)
