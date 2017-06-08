#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from classes.retriever import Retriever

stock_codes = ['1204']
retriever = Retriever()
read = retriever.readfiles_by_stock_codes(stock_codes)
for stock_code, line_number, line in read:
    check = retriever.check_condition_1(stock_code, line_number)
    if check:
        print(line_number, check)

