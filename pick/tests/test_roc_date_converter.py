#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import unittest
import datetime
from classes.roc_date_converter import RocDateConverter


class TestRocDatetime(unittest.TestCase):
    def setUp(self):
        self.roc_date_converter = RocDateConverter()

    def tearDown(self):
        self.roc_date_converter = None

    def test_get_datetime_in_roc(self):
        roc_date = '106/01/01'
        datetime_obj = self.roc_date_converter.get_datetime_in_roc(roc_date)
        self.assertEqual(datetime_obj.year, 2017)

    def test_get_roc_date_by_ad(self):
        ad_date = '2017/01/01'
        roc_date = self.roc_date_converter.get_roc_date_by_ad(ad_date)
        self.assertEqual(roc_date, '106/01/01')

    def test_get_ad_date_by_roc(self):
        roc_date = '106/01/01'
        ad_date = self.roc_date_converter.get_ad_date_by_roc(roc_date)
        self.assertEqual(ad_date, '2017/01/01')

    def test_get_roc_date_by_datetime(self):
        datetime_obj = datetime.datetime.strptime('2017/01/01', '%Y/%m/%d')
        roc_date = self.roc_date_converter.get_roc_date_by_datetime(datetime_obj)
        self.assertEqual(roc_date, '106/01/01')

if __name__ == '__main__':
    unittest.main()
