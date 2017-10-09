# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import json
import datetime

_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '{}/../../libs/src'.format(_dir))

from roc_date_converter import RocDateConverter

class Inventory():
    def __init__(self):
        self._dir = os.path.dirname(os.path.abspath(__file__))
        self.tse_data_dir = '{}/../../tse_crawler/data'.format(self._dir)
        self.reset_securities()


    def reset_securities(self):
        self.securities = {
            'normal': {},
            'margin': {},
            'short': {},
        }


    def store(self, inv_type, stock_code, date_obj, quantity):
        date_str = date_obj.strftime('%Y-%m-%d')
        buying_price = self.get_buying_price(stock_code, date_obj)
        if buying_price is None:
            raise InventoryException('找不到 {} 的價格資訊'.format(date_str))

        number = 0
        while quantity > number:
            number += 1
            securities_id = '{}{}{}'.format(stock_code, date_obj.strftime('%Y%m%d'), number)
            securities_data = {
                'id': securities_id,
                'date': date_str,
                'buying_price': buying_price,
            }
            try:
                self.securities[inv_type][stock_code]
            except KeyError:
                self.securities[inv_type][stock_code] = []
            self.securities[inv_type][stock_code].append(securities_data)


    def out(self, inv_type, stock_code, data_obj, quantity):
        secus = []
        i = 0
        while quantity > i:
            i += 1
            try:
                secu = self.securities[inv_type][stock_code].pop(0)
            except IndexError:
                raise InventoryException('庫存不足: {} - {}'.format(inv_type, stock_code))
            secus.append(secu)

        return secus


    def get_buying_price(self, stock_code, date_obj):
        # 檔名
        file_name = '{}/{}.csv'.format(self.tse_data_dir, stock_code)

        # 取得檔案內容
        f = open(file_name, 'r')
        file_content = f.read()
        f.close()

        # 找到該行資料
        converter = RocDateConverter()
        roc_date_str = converter.get_roc_date_by_datetime(date_obj)
        search_re = '{},[^,]*,[^,]*,([^,]*),[^,]*,[^,]*,[^,]*,[^,]*,[^,]*'.format(roc_date_str)
        search_result = re.search(search_re, file_content)

        # 取得買進價格
        try:
            buying_price = float(search_result.group(1))
        except AttributeError:
            return None

        return buying_price


class InventoryException(Exception):
    pass


def main():
    inv = Inventory()


if __name__ == '__main__':
    main()
