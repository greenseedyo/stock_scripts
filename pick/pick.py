#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from os import listdir, system
from os.path import join
import re
import sys
from classes.retriever import Retriever

def search_filename(filename):
    return re.search('^(\d{4}).csv$', filename)

def pick(date):
    data_path = '/Volumes/Backup Plus/stock/tsec/data/'
    file_list = (f for f in listdir(data_path) if search_filename(f) is not None)
    winners = []
    for filename in file_list:
        system('clear')
        print(filename)
        print(', '.join(winners))
        search_stock_code = re.search('(\w+).csv$', filename)
        stock_code = search_stock_code.group(1)
        retriever = Retriever()
        line_number = retriever.search_line_number_by_date(stock_code, date)
        if line_number is None:
            continue
        check = retriever.check_condition_1(stock_code, line_number)
        if check:
            winners.append(stock_code)

    return winners

def simulate(stock_codes, date):
    retriever = Retriever()
    for stock_code in stock_codes:
        print('股票編號: {}'.format(stock_code))
        data_set = retriever.simulate_rule_1(stock_code, date, 30)
        for data in data_set:
            print(data)
        break

def main():
    date = '101/06/08'
    winners = pick(date)
    #simulate(winners, date)

if __name__ == '__main__': main()

