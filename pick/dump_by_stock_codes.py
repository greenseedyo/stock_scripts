#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
from classes.retriever import Retriever

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stock_codes', nargs='*', help="股票代號")
    args = parser.parse_args()
    stock_codes = args.stock_codes

    #print(stock_codes)
    retriever = Retriever(stock_codes)
    retriever.put_mapping_by_stock_codes()
    retriever.dump_to_es()

if __name__ == '__main__': main()

