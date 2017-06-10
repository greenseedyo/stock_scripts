#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from os import listdir
from os.path import isfile, join
import re
import sys
from classes.retriever import Retriever

def search_filename(filename):
    return re.search('^(\d{4}).csv$', filename)

def main():
    retriever = Retriever()
    data_dir = retriever.data_dir
    file_list = (f for f in listdir(data_dir) if search_filename(f) is not None and int(search_filename(f).group(1)) > 3708)
    for filename in file_list:
        print(filename)
        search_stock_code = re.search('(\w+).csv$', filename)
        stock_code = search_stock_code.group(1)
        stock_codes = [stock_code]
        retriever.put_mapping_by_stock_codes()
        retriever.dump_to_es()

if __name__ == '__main__': main()
