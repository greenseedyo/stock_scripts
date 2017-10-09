# -*- coding: utf-8 -*-

import os
import sys
import datetime

_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append('{}/../../libs/src'.format(_dir))
from roc_date_converter import RocDateConverter
from tech_retriever import TechRetriever

class MA(object):
    @staticmethod
    def calculate(stock_code, date_obj, days_period):
        retriever = TechRetriever()
        roc_date_string = RocDateConverter().get_roc_date_by_datetime(date_obj)
        to_line_number = retriever.search_line_number_by_date(stock_code, roc_date_string)
        check = retriever.check_has_previous_data(to_line_number, days_period - 1)
        if not check:
            raise MAException('{} 日資料不足'.format(days_period))
        from_line_number = to_line_number - (days_period - 1)
        current = from_line_number
        total = 0
        while current <= to_line_number:
            line = retriever.get_line_by_number(stock_code, current)
            current += 1
            closing_price = float(retriever.get_line_data_dict(line)['closing_price'])
            total += closing_price
        ma = round(total / days_period, 2)
        return ma


class MAException(Exception):
    pass
