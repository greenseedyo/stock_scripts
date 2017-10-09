# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import logging
import requests
import json
import datetime

class Common():
    @staticmethod
    def get_stock_codes_from_tse(date_tuple):
        date_str = '{0}{1:02d}{2:02d}'.format(date_tuple[0], date_tuple[1], date_tuple[2])
        url = 'http://www.twse.com.tw/exchangeReport/MI_INDEX'

        query_params = {
            'date': date_str,
            'response': 'json',
            'type': 'ALL',
            '_': str(round(time.time() * 1000) - 500)
        }

        # Get json data
        page = requests.get(url, params=query_params)

        if not page.ok:
            logging.error("Can not get TSE data at {}".format(date_str))
            return

        content = page.json()

        try:
            content['data5']
        except KeyError:
            return

        stock_codes = []
        for data in content['data5']:
            stock_code = data[0].strip()
            if not re.search('^\d{4}$', stock_code):
                continue
            stock_codes.append(stock_code)

        return stock_codes


    @staticmethod
    def is_in_future(date_obj):
        if not date_obj.__class__.__name__ in ['date', 'datetime']:
            raise TypeError('argument #1 needs to be an "date" or "datetime" object')
        today = datetime.date.today().strftime("%Y-%m-%d")
        date_string = date_obj.strftime("%Y-%m-%d")
        if date_string > today:
            return True
        else:
            return False


if __name__ == '__main__':
    c = Common()
