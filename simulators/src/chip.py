# -*- coding: utf-8 -*-

import os
import re
import sys
import csv
import time
import datetime
import logging
import json
import math
from termcolor import colored, cprint

from src.bank import *
from src.rule import *
from src.criterias.short import *

_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append('{}/../../libs/src'.format(_dir))
from common import *
from roc_date_converter import RocDateConverter
from tech_retriever import TechRetriever
from ma import MA

class Chip():
    def __init__(self, rule=None, **kwargs):
        self._dir = os.path.dirname(os.path.abspath(__file__))
        self.chip_raw_data_dir = '{}/../../nvesto_crawler/raw_data'.format(self._dir)
        self.tech_data_dir = '{}/../../tse_crawler/data'.format(self._dir)
        self.sim_count = kwargs.pop('sim_count', 100)
        self.hold_max_days = kwargs.pop('hold_max_days', 14)
        self.stop_loss_factor = kwargs.pop('stop_loss_factor', 0.9)
        self.set_bank(Bank())
        if rule is not None:
            self.set_rule(rule)

    def set_bank(self, bank):
        if not isinstance(bank, Bank):
            raise ValueError('argument #1 must an instance of Rule');
        self.bank = bank

    def set_rule(self, rule):
        if not isinstance(rule, Rule):
            raise ValueError('argument #1 must an instance of Rule');
        self.rule = rule

    def simulate_all(self, first_date_obj):
        # 模擬開始日期
        first_date_tuple = (first_date_obj.year, first_date_obj.month, first_date_obj.day)
        cprint('模擬開始日期: {}'.format(first_date_tuple), 'green')
        # 取得所有股票代碼
        common = Common()
        stock_codes = common.get_stock_codes_from_tse(first_date_tuple)
        for stock_code in stock_codes:
            self.simulate_one(stock_code, first_date_obj)
            sys.exit(0)

    def simulate_one(self, stock_code, first_date_obj):
        i = 0
        counter = 0
        data_sets = []
        has_bought = False
        while counter < self.sim_count:
            date_obj = first_date_obj + datetime.timedelta(i)
            date_string = date_obj.strftime("%Y-%m-%d")
            print(stock_code, date_obj.year, date_obj.month, date_obj.day)
            i += 1
            if Common.is_in_future(date_obj):
                break
        
            one_day_data = self._get_one_day_data(stock_code, date_obj)

            if one_day_data is None:
                continue

            data_sets.append(one_day_data)

            # 是否達買進條件
            if not has_bought:
                if self.rule.check_buying_criteria(data_sets):
                    self.bank.margin_buy(stock_code, date_obj, quantity)

            # 是否達加碼買進條件
            if has_bought:
                if self.rule.check_buying_more_criteria(data_sets):
                    self.bank.margin_buy(stock_code, date_obj, quantity)

            # 是否達賣出條件
            if has_bought:
                if self.rule.check_selling_criteria(data_sets):
                    self.bank.margin_sell(stock_code, date_obj, quantity)

            # 是否達放空條件
            if not has_bought:
                if self.rule.check_shorting_criteria(data_sets):
                    print('符合放空條件: {} - {}'.format(stock_code, date_string))
                    quantity = 1
                    self.bank.short_sell(stock_code, date_obj, quantity)

            # 是否達加碼放空條件
            if has_bought:
                if self.rule.check_shorting_more_criteria(data_sets):
                    quantity = 1
                    self.bank.short_sell(stock_code, date_obj, quantity)

            # 是否達回補條件
            if has_bought:
                if self.rule.check_covering_criteria(data_sets):
                    quantity = 1
                    self.bank.short_cover(stock_code, date_obj, quantity)

            counter += 1

        accounting = self.bank.get_accounting(stock_code)
        print(accounting)

    def _get_one_day_data(self, stock_code, date_obj):
        periods = ('1day', '5days', '20days')
        major_force_net = {}
        for period in periods:
            try:
                raw_data = self._get_raw_data(stock_code, period, date_obj)
            except FileNotFoundError:
                return None
            major_force_net[period] = self._get_major_force_net(raw_data)

        volume_5days = math.floor(self._get_volume(stock_code, date_obj, 5) / 1000)
        volume_20days = math.floor(self._get_volume(stock_code, date_obj, 20) / 1000)
        con_5 = round(major_force_net['5days'] / volume_5days * 100, 2)
        con_20 = round(major_force_net['20days'] / volume_20days * 100, 2)
        closing_price = self._get_closing_price(stock_code, date_obj)
        ma_60 = self._get_ma_60(stock_code, date_obj)

        data = {
            'major_force_net': major_force_net['1day'],
            'concentration_5days': con_5,
            'concentration_20days': con_20,
            'closing_price': closing_price,
            'ma_60': ma_60,
        }
        return data

    def _get_major_force_net(self, raw_data):
        major_force_net = 0
        json_data = json.loads(raw_data)
        buy_data = json_data['data']['buy']
        for one_node in buy_data[:15]:
            major_force_net += round(float(one_node['net']))
        sell_data = json_data['data']['sell']
        for one_node in sell_data[:15]:
            major_force_net += round(float(one_node['net']))
        return major_force_net

    def _get_volume(self, stock_code, date_obj, days_period):
        roc_date_string = RocDateConverter().get_roc_date_by_datetime(date_obj)
        retriever = TechRetriever()
        to_line_number = retriever.search_line_number_by_date(stock_code, roc_date_string)
        check = retriever.check_has_previous_data(to_line_number, days_period - 1)
        if not check:
            raise ChipException('{} 日成交量資料不足'.format(days_period))
        from_line_number = to_line_number - (days_period - 1)
        current = from_line_number
        total_volume = 0
        while current <= to_line_number:
            line = retriever.get_line_by_number(stock_code, current)
            current += 1
            volume = int(retriever.get_line_data_dict(line)['volume'])
            total_volume += volume
        return total_volume

    def _get_closing_price(self, stock_code, date_obj):
        roc_date_string = RocDateConverter().get_roc_date_by_datetime(date_obj)
        retriever = TechRetriever()
        line_number = retriever.search_line_number_by_date(stock_code, roc_date_string)
        if line_number is None:
            raise ChipException('{} 找不到 {} 的資料'.format(stock_code, roc_date_string))
        line = retriever.get_line_by_number(stock_code, line_number)
        closing_price = float(retriever.get_line_data_dict(line)['closing_price'])
        return closing_price

    def _get_ma_60(self, stock_code, date_obj):
        ma = MA().calculate(stock_code, date_obj, 60)
        return ma

    def _get_stat_data(self, data):
        pass

    def _get_raw_data(self, stock_code, period, date_obj):
        date_string = date_obj.strftime("%Y-%m-%d")
        file_path = '{}/{}/{}/{}.txt'.format(self.chip_raw_data_dir, period, stock_code, date_string)
        if not os.path.isfile(file_path):
            raise FileNotFoundError()
        f = open(file_path, 'r')
        raw_data = f.read()
        f.close()
        return raw_data


class ChipException(Exception):
    pass


def main():
    # 模擬開始日
    from_date = '2017-09-01'
    # 模擬交易日數
    sim_count = 100
    # 單支股票持股交易日上限
    hold_max_days = 14
    # 停損設定
    stop_loss_factor = 0.90

    rule = Rule()

    shorting_criteria = DecreasingChip1()
    rule.set_shorting_criteria(shorting_criteria)

    shorting_more_criteria = DecreasingChip1()
    rule.set_shorting_more_criteria(shorting_more_criteria)

    covering_criteria = StopDecreasingChip1()
    rule.set_covering_criteria(covering_criteria)

    simulator = Chip(rule, sim_count=sim_count, hold_max_days=hold_max_days, stop_loss_factor=stop_loss_factor)

    from_date_obj = datetime.datetime.strptime(from_date, "%Y-%m-%d")
    first_date_obj = from_date_obj + datetime.timedelta(i)

    result = simulator.simulate_all(first_date_obj)


if __name__ == '__main__':
    main()
