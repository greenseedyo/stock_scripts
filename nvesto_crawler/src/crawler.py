# -*- coding: utf-8 -*-

import os
import re
import sys
import csv
import time
import logging
import requests
import argparse
import pycurl
import json
from random import randint
from time import sleep
from termcolor import colored, cprint
from datetime import datetime, timedelta
from subprocess import call
from io import BytesIO
from os import mkdir
from os.path import isdir
from http.cookies import SimpleCookie
from urllib.parse import urlencode

# https://duo.com/blog/driving-headless-chrome-with-python
from selenium import webdriver  
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Crawler():
    secret_token_site = 'localhost:8000'
    stock_codes = []
    major_force_json = {}
    date_picker_json = {}
    chrome_driver = ''
    csrf = ''

    def __init__(self):
        ''' Make directory if not exist when initialize '''
        crawler_dir = os.path.dirname(os.path.abspath(__file__))
        self.raw_data_dir = '{}/../raw_data'.format(crawler_dir)
        self.csv_data_dir = '{}/../csv_data'.format(crawler_dir)
        self.secret_token_site_dir = '{}/../secret_token_site'.format(crawler_dir)
        self.cookie_string_file = '{}/../cookie_string.txt'.format(crawler_dir)
        self.chrome_driver_path = '{}/../chromedriver'.format(crawler_dir)

        self._check_data_dirs_exist()


    def _check_data_dirs_exist(self):
        dirs = [
            self.raw_data_dir,
            '{}/1day'.format(self.raw_data_dir),
            '{}/5days'.format(self.raw_data_dir),
            '{}/20days'.format(self.raw_data_dir),
            self.csv_data_dir,
            '{}/1day'.format(self.csv_data_dir),
            '{}/5days'.format(self.csv_data_dir),
            '{}/20days'.format(self.csv_data_dir),
        ]
        for check_dir in dirs:
            if not isdir(check_dir):
                mkdir(check_dir)


    def _get_raw_data_file_dir(self, period, stock_code):
        file_dir = '{}/{}/{}'.format(self.raw_data_dir, period, stock_code)
        if not isdir(file_dir):
            mkdir(file_dir)
        return file_dir


    def main_loop(self, date_tuple):
        print('Crawling {}'.format(date_tuple))
        # 取得所有股票代碼
        self._set_stock_codes_from_tse(date_tuple)
        # 到 nvesto 爬資料
        date = '{0}-{1:02d}-{2:02d}'.format(date_tuple[0], date_tuple[1], date_tuple[2])

        self._set_chrome_driver()

        for stock_code in self.stock_codes:
            print('股票代碼 {}'.format(stock_code))
            try:
                raw_data = self.crawl_one_target(stock_code, date)
            except ValueError:
                print(self.date_picker_json['dateList'])
                sys.exit(0)

        self._unset_chrome_driver()


    def _record(self, stock_code, row):
        ''' Save row to csv file '''
        f = open('{}/{}.csv'.format(self.data_dir, stock_code), 'a')
        cw = csv.writer(f, lineterminator='\n')
        cw.writerow(row)
        f.close()


    def _set_stock_codes_from_tse(self, date_tuple):
        date_str = '{0}{1:02d}{2:02d}'.format(date_tuple[0], date_tuple[1], date_tuple[2])
        url = 'http://www.twse.com.tw/exchangeReport/MI_INDEX'

        query_params = {
            'date': date_str,
            'response': 'json',
            'type': 'ALL',
            '_': str(round(time.time() * 1000) - 500)
        }

        # Get json data
        page = requests.get(url, params=query_params)

        if not page.ok:
            logging.error("Can not get TSE data at {}".format(date_str))
            return

        content = page.json()

        try:
            content['data5']
        except KeyError:
            return

        for data in content['data5']:
            stock_code = data[0].strip()
            if not re.search('^\d{4}$', stock_code):
                continue
            self.stock_codes.append(stock_code)


    def _get_page_url_by_stock_code(self, stock_code):
        page_url = 'https://www.nvesto.com/tpe/{}/majorforce'.format(stock_code)
        return page_url


    def crawl_one_target(self, stock_code, date):
        if ('' == self.chrome_driver):
            self._set_chrome_driver()

        if (0 == len(self.date_picker_json)):
            page_url = self._get_page_url_by_stock_code(stock_code)
            print('Preparing date_picker_json from {}'.format(page_url))
            self._prepare_data_by_normal_page(page_url)

        dates_groups = self._get_trade_dates_groups(date)

        for period, from_date, to_date in dates_groups:
            file_dir = self._get_raw_data_file_dir(period, stock_code)
            file_path = '{}/{}.txt'.format(file_dir, date)
            if os.path.isfile(file_path):
                if os.stat(file_path).st_size:
                    continue

            try:
                raw_data = self._get_one_data_set(stock_code, from_date, to_date)
            except CrawlerCookieExpiredException:
                cprint('Cookie expired, refreshing cookie...', 'yellow')
                self.refresh_cookie()
                raw_data = self._get_one_data_set(stock_code, from_date, to_date)

            if ('true' == raw_data[8:12]):
                cprint('成功取得資料: {} 至 {} ({})'.format(from_date, to_date, period), 'green')
            else:
                raise CrawlerException('未知的資料格式: {}'.format(raw_data))

            print('寫入資料至 {} ...'.format(file_path))
            f = open(file_path, 'w+')
            f.write(raw_data)
            f.close()
            print('寫入完成')

            # 等候隨機秒數再進行下一次 request
            sleep_sec = randint(1, 5)
            print('等候 {} 秒 ...'.format(sleep_sec))
            sleep(sleep_sec)

        #sys.exit(0)


    def _get_trade_dates_groups(self, date):
        date_list = self.date_picker_json['dateList']
        index = date_list.index(date)
        _4_trade_days_ago = date_list[index - 4]
        _19_trade_days_ago = date_list[index - 19]

        dates_groups = [
            ('1day', date, date),
            ('5days', _4_trade_days_ago, date),
            ('20days', _19_trade_days_ago, date)
        ]
        return dates_groups


    def _get_one_data_set(self, stock_code, from_date, to_date):
        print('Trying to get data from {} to {} ...'.format(from_date, to_date))

        page_url = self._get_page_url_by_stock_code(stock_code)
        print('Preparing data from {}'.format(page_url))
        self._prepare_data_by_normal_page(page_url)
        cprint('Data prepared.'.format(page_url), 'green')

        csrf = self._get_csrf()
        print('csrf: {}'.format(csrf))
        secret_token = self._generate_secret_token(from_date, to_date)
        print('secret_token: {}'.format(secret_token))

        post_data = {
            "fromdate": from_date,
            "todate": to_date,
            "view": "detail",
            "csrf": csrf,
            "secretToken": secret_token
        }
        postfields = urlencode(post_data)
        headers = [
            'Origin: https://www.nvesto.com',
            'X-Requested-With: XMLHttpRequest',
        ]
        pycurl_options = [
            (pycurl.POST, 1),
            (pycurl.POSTFIELDS, postfields),
            (pycurl.COOKIE, self._get_cookie_string()),
            (pycurl.REFERER, '{}'.format(page_url)),
            (pycurl.HTTPHEADER, headers)
        ]
        ajax_data_url = 'https://www.nvesto.com{}'.format(self._get_ajax_data_url())
        body = self._get_html(ajax_data_url, pycurl_options)
        result = body.decode('utf-8')
        if '{"errMsg":"403","succ":false}' == result:
            raise CrawlerCookieExpiredException('cookie 已過期，請更新 cookie_string.txt')
        return result


    def _get_cookie_string(self):
        f = open(self.cookie_string_file)
        cookie = f.read(10000).strip()
        f.close()
        return cookie


    def _prepare_data_by_normal_page(self, page_url):
        cookie = self._get_cookie_string()
        pycurl_options = [
            (pycurl.COOKIE, cookie),
        ]
        body = self._get_html(page_url, pycurl_options)
        result = body.decode('utf-8')

        # 由 html 取得 MajorForce_JS_VARS 內容
        self._extract_major_force_json(result)
        # 由 html 取得 DATE_PICKER_JS_VARS 內容
        if 0 == len(self.date_picker_json):
            self._extract_date_picker_json(result)
        # 設定 csrf
        self._extract_csrf(result)


    def _extract_major_force_json(self, html):
        search = re.search('(MajorForce_JS_VARS=({.*?});)', html)
        major_force_string = search.group(1)
        json_string = search.group(2)
        if (0 == len(json_string)):
            raise CrawlerException('找不到 MajorForce_JS_VARS 內容')

        # 將 MajorForce_JS_VARS 內容寫入 secret_token_site/input.js
        mf_file = '{}/input.js'.format(self.secret_token_site_dir)
        f = open(mf_file, 'w')
        f.write(major_force_string)
        f.close()

        # 設定 self.major_force_json 變數
        try:
            self.major_force_json = json.loads(json_string)
        except json.decoder.JSONDecodeError:
            raise CrawlerException('MajorForce_JS_VARS 內容無法轉換成 JSON 格式')
        print('major_force_json prepared.')


    def _extract_date_picker_json(self, html):
        search = re.search('DATE_PICKER_JS_VARS=({.*?});', html)
        json_string = search.group(1)
        if (0 == len(json_string)):
            raise CrawlerException('找不到 DATE_PICKER_JS_VARS 內容')

        try:
            self.date_picker_json = json.loads(json_string)
        except json.decoder.JSONDecodeError:
            raise CrawlerException('DATE_PICKER_JS_VARS 內容無法轉換成 JSON 格式')
        print('date_picker_json prepared.')


    def _extract_csrf(self, response):
        new_csrf = re.search('"csrf":"([^"]*)"', response).group(1)
        if (0 == len(new_csrf)):
            cprint('未取得 csrf token', 'red')
        self.csrf = new_csrf


    def _get_csrf(self):
        return self.csrf


    def _get_ajax_data_url(self):
        try:
            url = self.major_force_json['dataUrl']
        except KeyError:
            raise CrawlerException('未設定 self.major_force_json 或抓不到 dataUrl')
        return url


    def _generate_secret_token(self, from_date, to_date):
        # 產生 secretToken
        # 必須先將 MajorForce_JS_VARS={...} 寫入 secret_token_site/input.js
        reset_url = "http://{}/reset.html".format(self.secret_token_site)
        secret_token_url = """http://{}/secret.html#!/fromdate/{}/todate/{}/view/detail""".format(self.secret_token_site, from_date, to_date)
        driver = self._get_chrome_driver()
        # 因為改變 hash 內容不會重新整理頁面，即使呼叫 driver.refresh() 也一樣，所以先開啟另一個網址做重置
        driver.get(reset_url)
        driver.get(secret_token_url)
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "secret"))
        )
        span = driver.find_element_by_id('secret')
        secret_token = span.text
        if (0 == len(secret_token)):
            raise CrawlerException('產生 secretToken 失敗')
        return secret_token


    def _get_html(self, url, pycurl_options=[]):
        bio = BytesIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.TIMEOUT, 10)
        c.setopt(pycurl.FOLLOWLOCATION, 1)
        c.setopt(pycurl.WRITEFUNCTION, bio.write)
        for key, value in pycurl_options:
            c.setopt(key, value)
        c.perform()
        body = bio.getvalue()
        return body


    def _set_chrome_driver(self):
        # 參考 https://duo.com/blog/driving-headless-chrome-with-python
        self.service = webdriver.chrome.service.Service(self.chrome_driver_path)
        self.service.start()

        chrome_options = Options()  
        #chrome_options.add_argument("--headless")  
        chrome_options.add_argument("--start-maximized")
        chrome_options.binary_location = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'
        #driver = webdriver.Chrome(executable_path=os.path.abspath("chromedriver"), chrome_options=chrome_options)
        self.chrome_driver = webdriver.Remote(self.service.service_url, desired_capabilities=chrome_options.to_capabilities())


    def _unset_chrome_driver(self):
        self.chrome_driver.close()


    def _get_chrome_driver(self):
        return self.chrome_driver


    def _get_cookie_dicts_from_file(self):
        f = open(self.cookie_string_file)
        cookie_string = f.read()
        f.close()
        cookie = SimpleCookie()
        cookie.load(cookie_string)
        cookie_dicts = []
        for key, morsel in cookie.items():
            cookie_dicts.append({'name': key, 'value': morsel.value})
        return cookie_dicts


    def _write_cookie_to_file(self, cookie_string):
        f = open(self.cookie_string_file, 'w+')
        f.write(cookie_string)
        f.close()


    def refresh_cookie(self):
        cookie_dicts = self._get_cookie_dicts_from_file()
        driver = self._get_chrome_driver()
        driver.get("https://www.nvesto.com/tpe/stockalert")
        for cookie_dict in cookie_dicts:
            driver.add_cookie(cookie_dict)
        driver.refresh()
        new_cookies = driver.get_cookies()
        new_cookie_array = []
        for new_cookie in new_cookies:
            string = '{}={}'.format(new_cookie['name'], new_cookie['value'])
            new_cookie_array.append(string)
        new_cookie_string = '; '.join(new_cookie_array)
        self._write_cookie_to_file(new_cookie_string)
        cprint('Cookie refreshed.', 'yellow')


    def login_nvesto(self):
        driver = self._get_chrome_driver()
        driver.get("https://www.nvesto.com/")

        login_xpath = '/html/body/div[1]/div[5]/div/a[6]/div'
        login_button = driver.find_element_by_xpath(login_xpath)
        if '登入' == login_button.text:
            print('找到登入按鈕，按下去...')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, login_xpath)))
            login_button.click()
        elif 'yo' != login_button.text:
            raise CrawlerException('帳號錯誤或無法登入')
        else:
            print('已登入')
            sys.exit(0)

        # 等登入表單出現
        print('等登入表單出現...')
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "LoginForm_email")))

        # 填入帳號密碼
        form_textfield = driver.find_element_by_xpath('//*[@id="LoginForm_email"]')
        form_textfield.send_keys("luyostudio@gmail.com")
        form_textfield = driver.find_element_by_id('//*[@id="LoginForm_password"]')
        form_textfield.send_keys("doesn't0MATTER!")
        form = driver.find_element_by_id("login-form")
        form.submit()

        # 等頁面重新整理
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="userlogin-click"]/div/div[2]')))
        finally:
            driver.quit()
            raise CrawlerException('登入帳號名稱未顯示')

        login_name = driver.find_element_by_css_selector(".nvestoLogin .h_menu_right")
        print(login_name.text)
        if 'yo' != login_name.text:
            raise CrawlerException('帳號錯誤或無法登入')

        #search_field = driver.find_element_by_id("site-search")
        #search_field.clear()
        #search_field.send_keys("Olabode")
        #search_field.send_keys(Keys.RETURN)
        login_name = driver.find_element_by_css_selector(".nvestoLogin .h_menu_right")
        print(login_name.text)
        #print(driver.page_source)
        driver.close()


def main():
    # Set logging
    log_dir = '{}/log'.format(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)
    filename = '{}/crawl-error.log'.format(log_dir)
    logging.basicConfig(filename=filename,
                        level=logging.ERROR,
                        format='%(asctime)s\t[%(levelname)s]\t%(message)s',
                        datefmt='%Y/%m/%d %H:%M:%S')

    # Get arguments
    parser = argparse.ArgumentParser(description='Crawl data at assigned day')
    parser.add_argument('day', type=int, nargs='*',
                        help='assigned day (format: YYYY MM DD), default is today')
    parser.add_argument('-b', '--back', action='store_true',
                        help='crawl back 1 year')
    parser.add_argument('-c', '--check', action='store_true',
                        help='crawl back 10 days for check data')

    args = parser.parse_args()

    # Day only accept 0 or 3 arguments
    if len(args.day) == 0:
        first_day = datetime.today()
    elif len(args.day) == 3:
        first_day = datetime(args.day[0], args.day[1], args.day[2])
    else:
        parser.error('Date should be assigned with (YYYY MM DD) or none')
        return

    crawler = Crawler()
    #crawler.crawl_one_target('1312', '2017-09-07')
    #sys.exit(0)

    # If back flag is on, crawl till 2014/2/11, else crawl one day
    if args.back or args.check:
        last_day = first_day - timedelta(365) if args.back else first_day - timedelta(10)
        max_error = 5
        error_times = 0

        while error_times < max_error and first_day >= last_day:
            try:
                crawler.main_loop((first_day.year, first_day.month, first_day.day))
                error_times = 0
            except Exception as e:
                date_str = first_day.strftime('%Y/%m/%d')
                logging.error('Crawl raise error {}: {}'.format(date_str, e))
                error_times += 1
                continue
            finally:
                first_day -= timedelta(1)
    else:
        crawler.main_loop((first_day.year, first_day.month, first_day.day))


class CrawlerException(Exception):
    pass


class CrawlerCookieExpiredException(Exception):
    pass


if __name__ == '__main__':
    main()
