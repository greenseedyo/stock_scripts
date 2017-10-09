# -*- coding: utf-8 -*-

from .context import *

import datetime
from src.common import Common

class TestCommon(unittest.TestCase):
    def test_get_stock_codes_from_tse(self):
        stock_codes = Common.get_stock_codes_from_tse((2017, 9, 7))
        self.assertEqual(912, len(stock_codes))


    def test_is_in_future(self):
        tomorrow_obj = datetime.date.today() + datetime.timedelta(1)
        self.assertTrue(Common.is_in_future(tomorrow_obj))

        with self.assertRaises(TypeError):
            Common.is_in_future('abc')
