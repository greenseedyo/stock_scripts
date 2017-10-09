# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import json
import datetime

from src.inventory import *

_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '{}/../../libs/src'.format(_dir))

from roc_date_converter import RocDateConverter

class Bank():
    fee_rate = 0.001425
    tax_rate = 0.003

    def __init__(self):
        self._dir = os.path.dirname(os.path.abspath(__file__))
        self.tse_data_dir = '{}/../../tse_crawler/data'.format(self._dir)
        self.inv = Inventory()

    def normal_buy(self, stock_code, date_obj, quantity):
        self.inventory.store('normal', stock_code, date_obj, quantity)

    def normal_sell(self, stock_code, data_obj, quantity):
        self.inventory.out('normal', stock_code, date_obj, quantity)

    def margin_buy(self, stock_code, date_obj, quantity):
        self.inventory.store('margin', stock_code, date_obj, quantity)

    def margin_sell(self, stock_code, date_obj, quantity):
        self.inventory.out('margin', stock_code, date_obj, quantity)

    def short_sell(self, stock_code, date_obj, quantity):
        self.inventory.out('short', stock_code, date_obj, quantity)

    def short_buy(self, stock_code, date_obj, quantity):
        self.inventory.store('short', stock_code, date_obj, quantity)

    def get_accounting(self, stock_code):
        pass


class BankException(Exception):
    pass


def main():
    bank = Bank()


if __name__ == '__main__':
    main()

