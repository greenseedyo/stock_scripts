#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os.path

class TechRetriever:
    line_pool = {}
    # data_dir = '/Volumes/Backup Plus/stock/tsec/data'
    data_dir = '/Users/yo/stock/stock_scripts/tse_crawler/data'

    def __init__(self, stock_codes=[]):
        self.stock_codes = stock_codes

    def set_stock_codes(self, stock_codes):
        self.stock_codes = stock_codes

    def get_filename_by_stock_code(self, stock_code):
        return '{}/{}.csv'.format(self.data_dir, stock_code)

    def readfiles_by_stock_codes(self, stock_codes):
        # check files exists first
        for stock_code in stock_codes:
            filename = self.get_filename_by_stock_code(stock_code)
            if not os.path.isfile(filename):
                raise RetrieverException('{} is not a file'.format(filename))
        for stock_code in stock_codes:
            line_number = 0
            f = open(filename)
            for line_raw in f:
                line_number += 1
                yield stock_code, line_number, line_raw
            f.close()

    def save_line(self, stock_code, line_number, line_raw):
        line = line_raw.strip()
        try:
            self.line_pool[stock_code][line_number] = line
        except KeyError:
            self.line_pool[stock_code] = {
                line_number: line
            }

    # 檢查是否有過去幾天的資料
    def check_has_previous_data(self, line_number, previous_days):
        return line_number > previous_days

    def get_line_by_number(self, stock_code, line_number):
        # get from pool if it has
        try:
            line = self.line_pool[stock_code][line_number]
            return line
        except KeyError:
            # get line from file
            filename = self.get_filename_by_stock_code(stock_code)
            fp = open(filename)
            for i, line_raw in enumerate(fp):
                if i == (line_number - 1):
                    self.save_line(stock_code, line_number, line_raw)
                    break
            fp.close()
            return self.line_pool[stock_code][line_number]

    def get_previous_valid_lines(self, stock_code, line_number, max_size):
        # get from pool if it has
        lines = []
        counter = 0
        i = 0
        while counter < max_size:
            i += 1
            previous_line_number = line_number - i
            if previous_line_number < 1:
                break
            line = self.get_line_by_number(stock_code, previous_line_number)
            data_dict = self.get_line_data_dict(line)
            try:
                float(data_dict['opening_price'])
            except ValueError:
                continue
            lines.append(line)
            counter += 1
        return lines

    def get_next_valid_lines(self, stock_code, line_number, max_size):
        # get from pool if it has
        lines = []
        counter = 0
        i = 0
        while counter < max_size:
            i += 1
            next_line_number = line_number + i
            line = self.get_line_by_number(stock_code, next_line_number)
            if line is None:
                break
            data_dict = self.get_line_data_dict(line)
            try:
                float(data_dict['opening_price'])
            except ValueError:
                continue
            lines.append(line)
            counter += 1
        return lines

    def get_previous_valid_closing_price(self, stock_code, line_number):
        previous_closing_price = 0
        previous_lines = self.get_previous_valid_lines(stock_code, line_number, 1)
        if len(previous_lines) < 1:
            raise RetrieverException('no previous line')
        previous_data_dict = self.get_line_data_dict(previous_lines[0])
        previous_closing_price = float(previous_data_dict['closing_price'])
        return previous_closing_price

    def get_difference(self, stock_code, line_number):
        try:
            previous_closing_price = self.get_previous_valid_closing_price(stock_code, line_number)
        except RetrieverException:
            return None
        line = self.get_line_by_number(stock_code, line_number)
        try:
            closing_price = float(self.get_line_data_dict(line)['closing_price'])
        except ValueError:
            return None
        difference = round(closing_price - previous_closing_price, 2)
        return difference

    def get_change_percent(self, stock_code, line_number):
        try:
            previous_closing_price = self.get_previous_valid_closing_price(stock_code, line_number)
        except RetrieverException:
            return None
        if 0 == previous_closing_price:
            return None
        difference = self.get_difference(stock_code, line_number)
        if difference is None:
            return None
        change_percent = difference / previous_closing_price
        return change_percent

    def get_line_data_dict(self, line):
        data = line.strip().split(',')
        dict = {
            'date': data[0],
            'volume': data[1],
            'turnover': data[2],
            'opening_price': data[3],
            'highest_price': data[4],
            'lowest_price': data[5],
            'closing_price': data[6],
            'difference': data[7],
            'transactions': data[8],
        }
        return dict

    def search_line_number_by_date(self, stock_code, date):
        filename = self.get_filename_by_stock_code(stock_code)
        f = open(filename)
        for i, line_raw in enumerate(f):
            line = line_raw.strip()
            if -1 != line.find(date):
                line_number = i + 1
                self.save_line(stock_code, line_number, line)
                break
        f.close()
        return line_number


class RetrieverException(Exception):
    pass

