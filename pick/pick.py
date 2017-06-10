#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from os import listdir, system
from os.path import join
import re
import sys
import datetime
from classes.retriever import Retriever

def search_filename(filename):
    return re.search('^(\d{4}).csv$', filename)

def pick(date_tw):
    retriever = Retriever()
    data_path = retriever.data_dir
    file_list = (f for f in listdir(data_path) if search_filename(f) is not None)
    winners = []
    for filename in file_list:
        #system('clear')
        #print('{} -- {}'.format(filename, ', '.join(winners)), end="\r")
        search_stock_code = re.search('(\w+).csv$', filename)
        stock_code = search_stock_code.group(1)
        line_number = retriever.search_line_number_by_date(stock_code, date_tw)
        if line_number is None:
            continue
        check = retriever.check_condition_1(stock_code, line_number)
        if check:
            winners.append(stock_code)

    return winners

def test_one(stock_code, date):
    retriever = Retriever()
    line_number = retriever.search_line_number_by_date(stock_code, date)
    check = retriever.check_condition_1(stock_code, line_number)

def simulate(stock_codes, date):
    # TODO: set max_days
    max_days = 3000
    retriever = Retriever()
    total_cost = 0
    total_revenue = 0
    total_roi = 0
    buy_in_unit = 1
    summary_set = []
    for stock_code in stock_codes:
        info = retriever.get_simulation_1_info(stock_code, date, max_days)
        cost = info['buy_in_price'] * 1000 * buy_in_unit
        total_cost += cost
        #print('股票編號: {}'.format(stock_code))
        data_set = info['data_set']
        end_price = 0
        sell_date = ''
        closing_price = 0
        roi = 0
        for data in data_set:
            #print(data)
            sell_date = data[0]
            closing_price = data[1]
            roi = data[2]
        revenue = closing_price * 1000 * buy_in_unit
        total_revenue += revenue
        #summary_set.append('股票編號: {}, 買進成本: {}, 賣出日期: {}, 賣出總價: {}'.format(stock_code, cost, sell_date, revenue))
    summary = '\n'.join(summary_set)
    total_roi = (total_revenue - total_cost) / total_cost
    formatted_roi = '{}%'.format(round(total_roi * 100, 2))
    formatted_cost = '{:,}'.format(total_cost)
    formatted_revenue = '{:,}'.format(total_revenue)
    print('模擬開始日期 {}, 結束日期 {}'.format(date, sell_date))
    #print(summary)
    print('總支出: {}, 總營收: {}, 投報率: {}'.format(formatted_cost, formatted_revenue, formatted_roi))

def main():
    start_date_tw = '106/04/02'
    start_date = '{}/{}/{}'.format(int(start_date_tw.split('/')[0]) + 1911, start_date_tw.split('/')[1], start_date_tw.split('/')[2])
    start_date_obj = datetime.datetime.strptime(start_date, "%Y/%m/%d")
    day_count = 30
    i = 0
    counter = 0
    while counter < day_count:
        date_obj = start_date_obj + datetime.timedelta(i)
        i += 1
        date = date_obj.strftime("%Y/%m/%d")
        date_tw = '{}/{}/{}'.format(int(date.split('/')[0]) - 1911, date.split('/')[1], date.split('/')[2])
        winners = pick(date_tw)
        #winners = [1707, 1802, 2008, 2230, 2477, 3048, 3051, 3141, 3434, 3455, 3516, 3556, 4543, 5383, 6105, 6569, 8446]
        try:
            simulate(winners, date_tw)
            counter += 1
        except Exception as e:
            #print('skip {}'.format(date_tw))
            continue

if __name__ == '__main__': main()

