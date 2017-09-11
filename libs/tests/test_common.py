# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import logging
import requests
import json
from datetime import datetime, timedelta

import unittest
from .context import Common

class TestCommon(unittest.TestCase):
    def test_get_stock_codes_from_tse(self):
        common = Common()
        stock_codes = common.get_stock_codes_from_tse((2017, 9, 7))
        self.assertEqual(912, len(stock_codes))

