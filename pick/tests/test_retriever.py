#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import unittest
from classes.retriever import *

class TestRetriever(unittest.TestCase):
    def setUp(self):
        self.retriever = Retriever()

    def tearDown(self):
        self.retriever = None

    def test_get_filename_by_stock_code(self):
        stock_code = '0050'
        filename = self.retriever.get_filename_by_stock_code(stock_code)
        self.assertEqual(filename, "{}/{}.csv".format(Retriever.data_dir, '0050'))

    def test_readfiles_by_stock_codes(self):
        # xxxx.csv 不存在，要噴 Exception
        stock_codes = ['0050', 'xxxx']
        with self.assertRaises(RetrieverException):
            data = self.retriever.readfiles_by_stock_codes(stock_codes)
            for stock_code, line_number, line in data:
                break
        # 檔案存在
        stock_codes = ['1204', '1212'] # 1204, 1212 已下市不會再有新的資料
        data = self.retriever.readfiles_by_stock_codes(stock_codes)
        stock_code = ''
        line_number = 0
        line = ''
        for stock_code, line_number, line in data:
            continue
        self.assertEqual(stock_code, '1212')
        self.assertEqual(line_number, 329)
        self.assertEqual(line, '94/06/03,254000,53340,0.21,0.21,0.21,0.21,-0.01,9\n')

    def test_save_line(self):
        stock_code = 'xxxx'
        line_number = 1
        line = 'test'
        self.retriever.save_line(stock_code, line_number, line)
        self.assertEqual(self.retriever.line_pool[stock_code][line_number], line)

    def test_check_has_previous_data(self):
        # 第 1 行前面沒資料
        line_number = 1
        previous_days = 1
        check = self.retriever.check_has_previous_data(line_number, previous_days)
        self.assertFalse(check, msg="1st line should have no previous line")
        # 第 3 行前面有 2 筆資料
        line_number = 3
        previous_days = 2
        check = self.retriever.check_has_previous_data(line_number, previous_days)
        self.assertTrue(check, msg="3rd line should have 2 previous lines")
        # 第 3 行前面沒有 3 筆資料
        line_number = 3
        previous_days = 3
        check = self.retriever.check_has_previous_data(line_number, previous_days)
        self.assertFalse(check, msg="3rd line shouldn't have 3 previous lines")

    def test_get_line_by_number(self):
        stock_code = '1204' # 1204 已下市不會再有新的資料
        line_number = 373
        line = self.retriever.get_line_by_number(stock_code, line_number)
        self.assertRegexpMatches(line, '94/09/09,0,0,--,--,--,--,,0')

    def test_get_previous_valid_lines(self):
        # 1204 第 261 行是空的，應該要跳過取得 260 行
        stock_code = '1204'
        line_number = 262
        max_size = 1
        lines = self.retriever.get_previous_valid_lines(stock_code, line_number, max_size)
        for line in lines:
            self.assertEqual(line, '94/02/23,25043,98216,3.96,3.98,3.90,3.97,-0.01,15')
        # 不足 max_size
        stock_code = '1204'
        line_number = 6
        max_size = 10
        lines = self.retriever.get_previous_valid_lines(stock_code, line_number, max_size)
        self.assertEqual(len(lines), 5)

    def test_get_next_valid_lines(self):
        # 1204 第 261 行是空的，應該要跳過取得 262 行
        stock_code = '1204'
        line_number = 260
        max_size = 1
        lines = self.retriever.get_next_valid_lines(stock_code, line_number, max_size)
        for line in lines:
            self.assertEqual(line, '94/02/25,42010,167609,3.98,4.00,3.98,3.98,X,17')
        # 不足 max_size
        stock_code = '1204'
        line_number = 371
        max_size = 10
        lines = self.retriever.get_next_valid_lines(stock_code, line_number, max_size)
        self.assertEqual(len(lines), 1)

    def test_get_previous_valid_closing_price(self):
        # 沒有之前的資料
        stock_code = '1204'
        line_number = 1
        with self.assertRaises(RetrieverException) as cm:
            previous_closing_price = self.retriever.get_previous_valid_closing_price(stock_code, line_number)
        the_exception = cm.exception
        self.assertEqual(str(the_exception), 'no previous line')

    def test_get_difference(self):
        # 沒有之前的資料
        stock_code = '1204'
        line_number = 1
        difference = self.retriever.get_difference(stock_code, line_number)
        self.assertIsNone(difference)
        # 有前一個交易日的資料
        stock_code = '1204'
        line_number = 2
        difference = self.retriever.get_difference(stock_code, line_number)
        self.assertEqual(difference, -0.50)
        # 前一個交易日暫停交易，抓前一個有效交易日的資料
        stock_code = '1204'
        line_number = 262
        difference = self.retriever.get_difference(stock_code, line_number)
        self.assertEqual(difference, 0.01)
        # 這個交易日暫停交易
        stock_code = '1204'
        line_number = 261
        difference = self.retriever.get_difference(stock_code, line_number)
        self.assertIsNone(difference)

    def test_get_change_percent(self):
        # 沒有之前的資料
        stock_code = '1204'
        line_number = 1
        change_percent = self.retriever.get_change_percent(stock_code, line_number)
        self.assertIsNone(change_percent)
        # 前一個交易日收盤價是 0
        stock_code = '2326'
        line_number = 47
        change_percent = self.retriever.get_change_percent(stock_code, line_number)
        self.assertIsNone(change_percent)
        # 有前一個交易日的資料
        stock_code = '1204'
        line_number = 2
        change_percent = self.retriever.get_change_percent(stock_code, line_number)
        self.assertEqual(round(change_percent, 4), -0.0690)
        # 前一個交易日暫停交易，抓前一個有效交易日的資料
        stock_code = '1204'
        line_number = 262
        change_percent = self.retriever.get_change_percent(stock_code, line_number)
        self.assertEqual(round(change_percent, 4), 0.0025)
        # 這個交易日暫停交易
        stock_code = '1204'
        line_number = 261
        change_percent = self.retriever.get_change_percent(stock_code, line_number)
        self.assertIsNone(change_percent)

    def test_get_line_data_dict(self):
        line = '94/02/03,2000,8000,4.00,4.00,4.00,4.00,0.07,2\r\n'
        data_dict = self.retriever.get_line_data_dict(line)
        assert_dict = {
            'date': '94/02/03',
            'volume': '2000',
            'turnover': '8000',
            'opening_price': '4.00',
            'highest_price': '4.00',
            'lowest_price': '4.00',
            'closing_price': '4.00',
            'difference': '0.07',
            'transactions': '2',
        }
        self.assertDictEqual(data_dict, assert_dict)

    def test_break_consolidation_area(self):
        # 不滿足預設參數條件
        stock_code = '1204'
        line_number = 20
        check = self.retriever.break_consolidation_area(stock_code, line_number)
        self.assertFalse(check)
        # 不滿足自訂參數條件
        stock_code = '4102'
        line_number = 44
        check = self.retriever.break_consolidation_area(stock_code, line_number, 10, 0.05)
        self.assertFalse(check)
        # 滿足預設參數條件
        stock_code = '1204'
        line_number = 44
        check = self.retriever.break_consolidation_area(stock_code, line_number)
        self.assertTrue(check)
        # 滿足自訂參數條件
        stock_code = '1204'
        line_number = 216
        check = self.retriever.break_consolidation_area(stock_code, line_number, 10, 0.09)
        self.assertTrue(check)

    def test_check_condition_1(self):
        # 不滿足此條件的
        stock_code = '1204'
        line_number = 20
        check = self.retriever.check_condition_1(stock_code, line_number)
        self.assertFalse(check)
        # 滿足此條件的
        stock_code = '1204'
        line_number = 229
        check = self.retriever.check_condition_1(stock_code, line_number, min_price = 4)
        self.assertTrue(check)
        # 暫停交易的
        stock_code = '1204'
        line_number = 261
        with self.assertRaises(RetrieverException) as cm:
            check = self.retriever.check_condition_1(stock_code, line_number)
        the_exception = cm.exception
        self.assertEqual(str(the_exception), 'no data')

    def test_search_line_by_date(self):
        stock_code = '1204'
        date = '94/09/09'
        line_number = self.retriever.search_line_number_by_date(stock_code, date)
        self.assertEqual(line_number, 373)

    def test_get_simulation_1_info(self):
        stock_code = '1204'
        date = '94/02/24'
        info = self.retriever.get_simulation_1_info(stock_code, date, 10)
        data_set = info['data_set']
        return_rate = ''
        for date, price, return_rate in data_set:
            continue
        self.assertEqual(info['pick_date'], '94/02/24')
        self.assertEqual(info['buy_in_price'], 3.98)
        self.assertEqual(return_rate, -0.0628)

if __name__ == '__main__':
    unittest.main()
