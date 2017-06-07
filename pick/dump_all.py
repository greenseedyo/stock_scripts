#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from os import listdir
from os.path import isfile, join
import re
import sys
from classes.dumpper import Dumpper

def search_filename(filename):
    return re.search('^(\d{4}).csv$', filename)

def main():
    data_path = '/Volumes/Backup Plus/stock/tsec/data/'
    file_list = (f for f in listdir(data_path) if search_filename(f) is not None and int(search_filename(f).group(1)) > 3708)
    for filename in file_list:
        print(filename)
        search_stock_code = re.search('(\w+).csv$', filename)
        stock_code = search_stock_code.group(1)
        stock_codes = [stock_code]
        dumpper = Dumpper(stock_codes)
        dumpper.put_mapping_by_stock_codes()
        dumpper.dump()

if __name__ == '__main__': main()
