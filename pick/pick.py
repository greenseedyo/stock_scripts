#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from os import listdir, system
from os.path import join
import re
import sys
from classes.dumpper import Dumpper

def search_filename(filename):
    return re.search('^(\d{4}).csv$', filename)

def main():
    data_path = '/Volumes/Backup Plus/stock/tsec/data/'
    file_list = (f for f in listdir(data_path) if search_filename(f) is not None)
    winner = []
    for filename in file_list:
        system('clear')
        print(filename)
        print(', '.join(winner))
        search_stock_code = re.search('(\w+).csv$', filename)
        stock_code = search_stock_code.group(1)
        dumpper = Dumpper()
        line_number = dumpper.search_line_number_by_date(stock_code, '101/06/18')
        if line_number is None:
            continue
        check = dumpper.check_condition_1(stock_code, line_number)
        if check:
            winner.append(stock_code)

if __name__ == '__main__': main()

