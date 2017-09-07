# -*- coding: utf-8 -*-

from crawl import Crawler
import unittest


class TestCrawler(unittest.TestCase):
    def setUp(self):
        self.crawler = Crawler()

    def tearDown(self):
        self.crawler = None

    def test_get_html(self):
        # get
        url = 'https://www.google.com.tw'
        result = self.crawler.get_html(url)
        self.assertEqual('<!doctype html>', result[:15])
        # TODO: post
        # TODO: cookie

