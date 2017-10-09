# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import datetime


# all date format must be yyy/mm/dd for roc date, and yyyy/mm/dd for ad date
class RocDateConverter():
    def get_datetime_in_roc(self, roc_date):
        info = roc_date.split('/')
        ad_date = '{}/{}/{}'.format(int(info[0]) + 1911, info[1], info[2])
        datetime_obj = datetime.datetime.strptime(ad_date, '%Y/%m/%d')
        return datetime_obj

    def get_roc_date_by_ad(self, ad_date):
        datetime_obj = datetime.datetime.strptime(ad_date, '%Y/%m/%d')
        roc_date = self.get_roc_date_by_datetime(datetime_obj)
        return roc_date

    def get_ad_date_by_roc(self, roc_date):
        datetime_obj = self.get_datetime_in_roc(roc_date)
        return datetime_obj.strftime('%Y/%m/%d')

    def get_roc_date_by_datetime(self, datetime_obj):
        info = datetime_obj.strftime('%Y/%m/%d').split('/')
        roc_date = '{}/{}/{}'.format(int(info[0]) - 1911, info[1], info[2])
        return roc_date
