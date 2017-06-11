#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from os import listdir, system
from os.path import join
import re
import sys
import datetime
from classes.retriever import Retriever, RetrieverException
from classes.roc_date_converter import RocDateConverter


def search_filename(filename):
    return re.search('^(\d{4}).csv$', filename)


def pick(date_obj, **kwargs):
    date_tw = RocDateConverter().get_roc_date_by_datetime(date_obj)
    min_volume = kwargs.pop('min_volume', 1 * 1000)
    max_volume = kwargs.pop('max_volume', 10 * 1000)
    min_price = kwargs.pop('min_price', 12)
    max_price = kwargs.pop('max_price', 1000)
    min_change_percent = kwargs.pop('min_chagne_percent', 0.03)
    consolidation_days = kwargs.pop('consolidation_days', 20)
    retriever = Retriever()
    data_path = retriever.data_dir
    file_list = (f for f in listdir(data_path) if search_filename(f) is not None)
    winners = []
    for filename in file_list:
        # system('clear')
        # print('{} -- {}'.format(filename, ', '.join(winners)), end="\r")
        search_stock_code = re.search('(\w+).csv$', filename)
        stock_code = search_stock_code.group(1)
        line_number = retriever.search_line_number_by_date(stock_code, date_tw)
        if line_number is None:
            continue
        try:
            check = retriever.check_model_1(stock_code, line_number,
                                            min_volume=min_volume,
                                            max_volume=max_volume,
                                            min_price=min_price,
                                            max_price=max_price,
                                            min_change_percent=min_change_percent,
                                            consolidation_days=consolidation_days)
        except RetrieverException:
            continue
        if check:
            winners.append(stock_code)

    return winners


def test_one(stock_code, date):
    retriever = Retriever()
    line_number = retriever.search_line_number_by_date(stock_code, date)
    check = retriever.check_model_1(stock_code, line_number)
    print(check)


def simulate(stock_codes, pick_date_obj, max_days, stop_loss_factor):
    retriever = Retriever()
    total_cost = 0
    total_revenue = 0
    total_roi = 0
    buy_in_unit = 1
    # summary_set = []
    stop_loss_count = 0
    # 開始買進時間
    start_date_obj = None
    start_date_tw = ''
    end_date_obj = None
    end_date_tw = ''
    max_through_days = 0
    pick_date_tw = RocDateConverter().get_roc_date_by_datetime(pick_date_obj)
    for stock_code in stock_codes:
        info = retriever.get_simulation_1_info(stock_code, pick_date_tw,
                                               max_days, stop_loss_factor)
        spend = info['buy_in_price'] * 1000 * buy_in_unit
        buying_fee = max(spend * 0.001425 * 0.65, 20)
        cost = spend + buying_fee
        total_cost += cost
        # print('股票編號: {}'.format(stock_code))
        data_set = info['data_set']
        if len(data_set) < max_days:
            stop_loss_count += 1
        closing_price = 0
        for data in data_set:
            # print(data)
            date_tw = data[0]
            date_obj = RocDateConverter().get_datetime_in_roc(date_tw)
            if (start_date_obj is None) or (date_obj < start_date_obj):
                start_date_obj = date_obj
                start_date_tw = date_tw
            if (end_date_obj is None) or (date_obj > end_date_obj):
                end_date_obj = date_obj
                end_date_tw = date_tw
            closing_price = data[1]
        income = closing_price * 1000 * buy_in_unit
        selling_fee = max(income * 0.001425 * 0.65, 20)
        tax = income * 0.003
        revenue = income - selling_fee - tax
        total_revenue += revenue
        timedelta = end_date_obj - start_date_obj
        through_days = timedelta.days + 1
        if through_days > max_through_days:
            max_through_days = through_days
        # summary_set.append('股票編號: {}, 買進成本: {}, 賣出日期: {}, 賣出總價: {}'.format(stock_code, cost, end_date_tw, revenue))
    # summary = '\n'.join(summary_set)
    total_roi = (total_revenue - total_cost) / total_cost
    formatted_roi = '{}%'.format(round(total_roi * 100, 2))
    formatted_cost = '{:,.0f}'.format(total_cost)
    net = total_revenue - total_cost
    formatted_net = '{:,.0f}'.format(net)
    pick_date = pick_date_obj.strftime("%Y/%m/%d")
    print('選股日期 {}, 開始日期 {}, 結束日期 {}, 停損 {}/{}'
          .format(pick_date, start_date_tw, end_date_tw, stop_loss_count, len(stock_codes)))
    # print(summary)
    print('總成本: {}, 利潤: {}, 投報率: {}\n'
          .format(formatted_cost, formatted_net, formatted_roi))
    result = {
        'roi': total_roi,
        'cost': total_cost,
        'net': net,
        'days': max_through_days,
        'formatted_data_dict': {
            'pick_date': pick_date,
            'start_date_tw': start_date_tw,
            'end_date_tw': end_date_tw,
            'pick_count': len(stock_codes),
            'stop_loss_count': stop_loss_count,
            'cost': formatted_cost,
            'net': formatted_net,
            'roi': formatted_roi,
        }
    }
    return result


def main():
    # 模擬開始日
    from_date = '2014/04/01'
    # 模擬進場次數
    day_count = 100
    # 單支股票持股交易日上限
    max_days = 90
    # 停損設定
    stop_loss_factor = 0.90
    # 選股設定 - model_1
    min_volume = 1000 * 1000
    max_volume = None  # 500 * 1000
    min_price = 12
    max_price = 200
    min_change_percent = 0.03
    consolidation_days = 10

    from_date_obj = datetime.datetime.strptime(from_date, "%Y/%m/%d")
    i = 0
    counter = 0
    wins = []
    loses = []
    sum_net = 0
    sum_cost = 0
    sum_days = 0
    today = datetime.date.today().strftime("%Y/%m/%d")
    while counter < day_count:
        pick_date_obj = from_date_obj + datetime.timedelta(i)
        pick_date = pick_date_obj.strftime("%Y/%m/%d")
        i += 1
        if pick_date == today:
            break
        winners = pick(pick_date_obj,
                       min_volume=min_volume,
                       max_volume=max_volume,
                       min_price=min_price,
                       max_price=max_price,
                       min_change_percent=min_change_percent,
                       consolidation_days=consolidation_days)
        if 0 == len(winners):
            print('{} 無符合條件的股票\n'.format(pick_date))
            continue
        try:
            result = simulate(winners, pick_date_obj, max_days, stop_loss_factor)
            roi = result['roi']
            net = result['net']
            cost = result['cost']
            days = result['days']
            sum_net += net
            sum_cost += cost
            sum_days += days
            if roi > 0:
                wins.append(roi)
            else:
                loses.append(roi)
            counter += 1
        except RetrieverException as e:
            #print('skip {}'.format(date_tw))
            continue
    if 0 == counter:
        print('無結果')
        sys.exit(0)
    wins.sort(reverse=True)
    loses.sort()
    wins_count = len(wins)
    loses_count = len(loses)
    win_rate = round(float(wins_count) / float(wins_count + loses_count), 4)
    avg_cost = int(sum_cost / counter)
    avg_days = int(sum_days / counter)
    expected_net = int(sum_net / counter)
    expected_roi = sum_net / sum_cost
    expected_annualized_roi = expected_roi / avg_days * 365
    print('模擬次數: {}'.format(counter))
    print('勝 {}: {}'.format(wins_count, ', '.join('{}%'.format(round(roi * 100, 2)) for roi in wins)))
    print('負 {}: {}'.format(loses_count, ', '.join('{}%'.format(round(roi * 100, 2)) for roi in loses)))
    print('勝率: {}%'.format(win_rate * 100, ".2f"))
    print('平均成本: {}'.format(avg_cost))
    print('利潤期望值: {}'.format(expected_net))
    print('投報率期望值: {}%'.format(round(expected_roi * 100, 2)))
    print('平均持股天數: {}'.format(avg_days))
    print('年化投報率期望值: {}%'.format(round(expected_annualized_roi * 100, 2)))

if __name__ == '__main__':
    main()
