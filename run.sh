#!/bin/bash
# tse crawler
TSE_CRAWLER_PATH="./tse_crawler"
/usr/bin/python $TSE_CRAWLER_PATH/crawl.py --check
/usr/bin/python $TSE_CRAWLER_PATH/post_process.py
