# -*- coding: utf-8 -*-

import os
import re
import sys
import csv
import time
import logging
import requests
import argparse
import pycurl
import json
from termcolor import colored, cprint
from datetime import datetime, timedelta
from subprocess import call
from io import BytesIO
from os import mkdir
from os.path import isdir
from http.cookies import SimpleCookie
from urllib.parse import urlencode

# https://duo.com/blog/driving-headless-chrome-with-python
from selenium import webdriver  
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import unittest
from .context import Crawler


class TestCrawler(unittest.TestCase):
    def setUp(self):
        self.tests_dir = os.path.dirname(os.path.abspath(__file__))
        self.crawler = Crawler()

    def tearDown(self):
        self.crawler = None

    def test_get_html(self):
        # get
        url = 'https://www.google.com.tw'
        body = self.crawler._get_html(url)
        result = body.decode('ISO-8859-1')
        self.assertEqual('<!doctype html>', result[:15])
        # TODO: post
        # TODO: cookie


    def test_get_trade_dates_groups(self):
        self.crawler.date_picker_json = self._get_date_picker_json_sample()
        date = '2017-09-08'
        dates_groups = self.crawler._get_trade_dates_groups(date)
        self.assertEqual('1day', dates_groups[0][0])
        self.assertEqual('2017-09-08', dates_groups[0][1])
        self.assertEqual('2017-09-08', dates_groups[0][2])
        self.assertEqual('5days', dates_groups[1][0])
        self.assertEqual('2017-09-04', dates_groups[1][1])
        self.assertEqual('2017-09-08', dates_groups[1][2])
        self.assertEqual('20days', dates_groups[2][0])
        self.assertEqual('2017-08-14', dates_groups[2][1])
        self.assertEqual('2017-09-08', dates_groups[2][2])


    def test_extract_csrf(self):
        html = self._get_sample_html()
        self.crawler._extract_csrf(html)
        self.assertEqual('wiyIZZ-vUE9ptnUcUZhYEA_O8joHon4UWedira6ud7qnMBQuYV29K_1oQy3fPBTIewR9FIYkK6FzKGSlnuwu1uqvK7Ar05ju', self.crawler._get_csrf())


    def test_get_raw_data_file_dir(self):
        stock_code = '0050'
        period = '1day'
        file_dir = self.crawler._get_raw_data_file_dir(period, stock_code)
        self.assertEqual(os.path.abspath('{}/../raw_data/1day/0050'.format(self.tests_dir)), os.path.abspath(file_dir))


    def _get_date_picker_json_sample(self):
        f = open('{}/sample_date_picker_string.txt'.format(self.tests_dir), 'r')
        string = f.read()
        f.close()
        return json.loads(string)


    def _get_sample_html(self):
        f = open('{}/sample_html.txt'.format(self.tests_dir), 'r')
        html = f.read()
        f.close()
        return html


if __name__ == '__main__':
    unittest.main()
