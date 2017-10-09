# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import json
import datetime

from .context import *

class TestInventory(unittest.TestCase):
    def setUp(self):
        self.tests_dir = os.path.dirname(os.path.abspath(__file__))
        self.inv = Inventory()


    def tearDown(self):
        self.inv = None


    def test_reset_securities(self):
        self.inv.reset_securities()
        self.assertDictEqual({}, self.inv.securities['normal'])
        self.assertDictEqual({}, self.inv.securities['margin'])
        self.assertDictEqual({}, self.inv.securities['short'])


    def test_store(self):
        # 重置 securities
        self.inv.reset_securities()

        # 正常
        stock_code = '0050'
        date = '2017-06-09'
        date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
        quantity = 2
        self.inv.store('normal', stock_code, date_obj, quantity)
        self.assertEqual(2, len(self.inv.securities['normal'][stock_code]))
        secu_1 = self.inv.securities['normal'][stock_code].pop(0)
        self.assertEqual('0050201706091', secu_1['id'])
        self.assertEqual('2017-06-09', secu_1['date'])
        self.assertEqual(78.05, secu_1['buying_price'])
        secu_2 = self.inv.securities['normal'][stock_code].pop(0)
        self.assertEqual('0050201706092', secu_2['id'])
        self.assertEqual('2017-06-09', secu_2['date'])
        self.assertEqual(78.05, secu_2['buying_price'])

        # 日期不對
        stock_code = '0050'
        date = '1111-11-11'
        date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
        quantity = 2
        with self.assertRaises(InventoryException):
            self.inv.store('normal', stock_code, date_obj, quantity)


    def test_out(self):
        # 重置 securities
        self.inv.reset_securities()

        stock_code = '0050'
        date = '2017-06-09'
        date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
        quantity = 2
        self.inv.store('normal', stock_code, date_obj, quantity)

        # 取出庫存
        secus = self.inv.out('normal', stock_code, date_obj, quantity)
        secu_1 = secus.pop(0)
        self.assertEqual('0050201706091', secu_1['id'])
        self.assertEqual('2017-06-09', secu_1['date'])
        self.assertEqual(78.05, secu_1['buying_price'])
        secu_2 = secus.pop(0)
        self.assertEqual('0050201706092', secu_2['id'])
        self.assertEqual('2017-06-09', secu_2['date'])
        self.assertEqual(78.05, secu_2['buying_price'])

        # 庫存不足
        quantity = 1
        with self.assertRaises(InventoryException):
            secus = self.inv.out('normal', stock_code, date_obj, quantity)


    def test_get_buying_price(self):
        stock_code = '0050'
        date = '2017-06-09'
        date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
        buying_price = self.inv.get_buying_price(stock_code, date_obj)
        self.assertEqual(78.05, buying_price)


if __name__ == '__main__':
    unittest.main()
