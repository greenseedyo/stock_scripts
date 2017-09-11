# -*- coding: utf-8 -*-

import os
import re
import sys
import csv
import time
import json

import unittest
from .context import Formatter

class TestCrawler(unittest.TestCase):
    def setUp(self):
        self.tests_dir = os.path.dirname(os.path.abspath(__file__))
        self.crawler = Crawler()

    def tearDown(self):
        self.crawler = None

