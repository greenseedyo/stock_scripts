#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
from classes.dumpper import Dumpper

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stock_codes', nargs='*', help="股票代號")
    args = parser.parse_args()
    stock_codes = args.stock_codes

    #print(stock_codes)
    dumpper = Dumpper(stock_codes)
    dumpper.put_mapping_by_stock_codes()
    dumpper.dump()

if __name__ == '__main__': main()

