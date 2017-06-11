#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import os.path
from elasticsearch import Elasticsearch

reload(sys)  
sys.setdefaultencoding('utf8')

class Retriever:
    line_pool = {}
    index_name = 'tsec'
    #data_dir = '/Volumes/Backup Plus/stock/tsec/data'
    data_dir = '/Users/yo/stock/data'

    def __init__(self, stock_codes = []):
        self.es = Elasticsearch(timeout=30)
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
            for line_raw in open(filename):
                line_number += 1
                yield stock_code, line_number, line_raw

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

    def break_consolidation_area(self, stock_code, line_number, period = 5, threshold = 0.08):
        peroid_highest = 0
        peroid_lowest = 10000
        previous_valid_lines = self.get_previous_valid_lines(stock_code, line_number, period)
        if len(previous_valid_lines) < period:
            return False
        for previous_line in previous_valid_lines:
            data_dict = self.get_line_data_dict(previous_line)
            try:
                highest_price = float(data_dict['highest_price'])
                lowest_price = float(data_dict['lowest_price'])
                if highest_price > peroid_highest:
                    peroid_highest = highest_price
                if lowest_price < peroid_lowest:
                    peroid_lowest = lowest_price
            except ValueError:
                continue
        peroid_difference = peroid_highest - peroid_lowest
        # 價差超過 threshold 就不算盤整區
        if peroid_difference / peroid_lowest > threshold:
            return False
        line = self.get_line_by_number(stock_code, line_number)
        closing_price = float(self.get_line_data_dict(line)['closing_price'])
        if closing_price > peroid_highest:
            return True

    # 條件一：
    # (1) 成交量大於 1000，並超過 5 日均量的 2 倍
    # (2) 股價設定區間
    # (3) 漲半支停板以上
    # (4) 突破盤整區
    def check_condition_1(self, stock_code, line_number, **kwargs):
        # 條件設定
        threshold_min_volume = kwargs.pop('min_volume', 1000)
        threshold_min_price = kwargs.pop('min_price', 20)
        threshold_max_price = kwargs.pop('max_price', 50)
        threshold_min_change_percent = kwargs.pop('min_chagne_percent', 0.03)

        line = self.get_line_by_number(stock_code, line_number)
        data_dict = self.get_line_data_dict(line)
        volume = int(data_dict['volume'])
        try:
            closing_price = float(data_dict['closing_price'])
        except ValueError:
            raise RetrieverException('no data')
        # 成交量門檻
        if volume < threshold_min_volume:
            return False
        # 股價門檻
        if closing_price < threshold_min_price:
            return False
        if closing_price > threshold_max_price:
            return False
        # 漲幅是否門檻
        change_percent = self.get_change_percent(stock_code, line_number)
        if not isinstance(change_percent, float):
            return False
        if change_percent < threshold_min_change_percent:
            return False
        # 是否有過去 5 天的資料
        check = self.check_has_previous_data(line_number, 5)
        if not check:
            return False
        # 計算 5 日總量
        sum_volume_5days = 0
        previous_lines = self.get_previous_valid_lines(stock_code, line_number, 5)
        if len(previous_lines) < 5:
            return False
        for previous_line in previous_lines:
            previous_data_dict = self.get_line_data_dict(previous_line)
            sum_volume_5days += int(previous_data_dict['volume'])
        # 計算 5 日均量的 2 倍
        double_5days_avg = int(sum_volume_5days / 5 * 2)

        if not volume > double_5days_avg:
            return False

        # 是否突破盤整區
        if not self.break_consolidation_area(stock_code, line_number, 10):
            return False

        return True


    def search_line_number_by_date(self, stock_code, date):
        filename = self.get_filename_by_stock_code(stock_code)
        for i, line_raw in enumerate(open(filename)):
            line = line_raw.strip()
            if -1 != line.find(date):
                line_number = i + 1
                self.save_line(stock_code, line_number, line)
                return line_number

    def get_simulation_1_info(self, stock_code, pick_date, max_days = 30):
        info = {
            'pick_date': pick_date,
            'buy_in_price': 0,
            'data_set': []
        }
        line_number = self.search_line_number_by_date(stock_code, pick_date)
        if line_number is None:
            raise RetrieverException('找不到 {} 的資料'.format(pick_date))
        # 抓選股日之後的資料 (選股日不算)
        lines = self.get_next_valid_lines(stock_code, line_number, max_days)
        # 移動停損點法，停損點設定
        stop_loss_factor = 0.9
        highest_price = 0
        for i, line in enumerate(lines):
            data_dict = self.get_line_data_dict(line)
            # 第一天開盤價進場
            if 0 == i:
                buy_in_price = float(data_dict['opening_price'])
                info['buy_in_price']= buy_in_price
            if float(data_dict['highest_price']) > highest_price:
                highest_price = float(data_dict['highest_price'])
            closing_price = float(data_dict['closing_price'])
            current_line_number = i + 1
            roi = round((closing_price - buy_in_price) / buy_in_price, 4)
            data = [data_dict['date'], closing_price, roi]
            info['data_set'].append(data)
            # 是否跌破停損點
            if closing_price < highest_price * stop_loss_factor:
                break
        return info


    def dump_to_es(self):
        bulk_size = 1000
        counter = 0
        querys = []
        print("dumpping '%s' ..." % (', '.join(self.stock_codes)))
        for stock_code, line_number, line in self.readfiles_by_stock_codes(self.stock_codes):
            self.save_line(stock_code, line_number, line)
            data_dict = self.get_line_data_dict(line)
            year = int(data_dict['date'].split('/')[0]) + 1911
            month = data_dict['date'].split('/')[1]
            day = data_dict['date'].split('/')[2]
            date_str = '{}-{}-{}'.format(year, month, day)
            date_id = '{}{}{}'.format(year, month, day)
            volume = int(data_dict['volume']) # 成交量
            try:
                opening_price = float(data_dict['opening_price'])
                highest_price = float(data_dict['highest_price'])
                lowest_price = float(data_dict['lowest_price'])
                closing_price = float(data_dict['closing_price'])
                difference = self.get_difference(stock_code, line_number)
                condition_1 = self.check_condition_1(stock_code, line_number)
            except ValueError:
                continue

            dump_dict = {
                "股票代碼": stock_code,
                "交易日期": date_str,
                "成交股數": volume,
                "成交金額": data_dict['turnover'],
                "開盤價": opening_price,
                "最高價": highest_price,
                "最低價": lowest_price,
                "收盤價": closing_price,
                "漲跌價差": difference,
                "成交筆數": data_dict['transactions'],
                "自訂條件1": '是' if condition_1 else '否',
            }

            querys.append({
                "index": {
                    "_index": self.index_name,
                    "_type": stock_code,
                    "_id": date_id
                }
            })
            querys.append(dump_dict)
            counter += 1
            if counter == bulk_size:
                self.bulk_to_es(querys)
                querys = []

        # last bulk
        if len(querys) > 0:
            self.bulk_to_es(querys)

    def bulk_to_es(self, request_body):
        res = self.es.bulk(index = self.index_name, body = request_body)
        #print(" response: '%s'" % (res))

    def put_mapping_by_stock_codes(self):
        # put mappings
        for stock_code in self.stock_codes:
            request_body = {
                "properties": {
                    "股票代碼": {
                        "type": "string",
                        "index": "not_analyzed"
                    },
                    "自訂組合名稱": {
                        "type": "string",
                        "index": "not_analyzed"
                    },
                    "交易日期": {
                        "type": "date",
                        "index": "true"
                    },
                    "成交股數": {
                        "type": "long",
                        "index": "true"
                    },
                    "成交金額": {
                        "type": "long",
                        "index": "true"
                    },
                    "開盤價": {
                        "type": "float",
                        "index": "true"
                    },
                    "最高價": {
                        "type": "float",
                        "index": "true"
                    },
                    "最低價": {
                        "type": "float",
                        "index": "true"
                    },
                    "收盤價": {
                        "type": "float",
                        "index": "true"
                    },
                    "漲跌價差": {
                        "type": "float",
                        "index": "true"
                    },
                    "漲跌幅": {
                        "type": "float",
                        "index": "true"
                    },
                    "成交筆數": {
                        "type": "long",
                        "index": "true"
                    },
                    "自訂條件1": {
                        "type": "string",
                        "index": "not_analyzed"
                    }
                }
            }
            doc_type = stock_code
            #print("putting mapping of '%s' ..." % (doc_type))
            res = self.es.indices.put_mapping(index = self.index_name, doc_type = doc_type, body = request_body)
            #print(" response: '%s'" % (res))

class RetrieverException(Exception):
    pass
