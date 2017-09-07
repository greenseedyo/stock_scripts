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
from datetime import datetime, timedelta
from subprocess import call
from io import BytesIO
from os import mkdir
from os.path import isdir
from http.cookies import SimpleCookie

# https://duo.com/blog/driving-headless-chrome-with-python
from selenium import webdriver  
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Crawler():
    crawler_dir = os.path.dirname(os.path.abspath(__file__))
    stock_codes = []
    cookie_string_file = 'cookie_string.txt'
    major_force_json = {}

    def __init__(self, prefix="data"):
        ''' Make directory if not exist when initialize '''
        self.data_dir = '{}/{}'.format(self.crawler_dir, prefix)
        if not isdir(self.data_dir):
            mkdir(self.data_dir)
        self.set_chrome_driver()

    def __exit__(self, exc_type, exc_value, traceback):
        self.unset_chrome_driver()

    def _record(self, stock_id, row):
        ''' Save row to csv file '''
        f = open('{}/{}.csv'.format(self.data_dir, stock_id), 'a')
        cw = csv.writer(f, lineterminator='\n')
        cw.writerow(row)
        f.close()

    def set_stock_codes_from_tse(self, date_tuple):
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

    def get_data(self, date_tuple):
        print('Crawling {}'.format(date_tuple))
        # get stock codes from tse
        self.set_stock_codes_from_tse(date_tuple)
        # get data from nvesto
        date_str = '{0}-{1:02d}-{2:02d}'.format(date_tuple[0], date_tuple[1], date_tuple[2])
        for stock_code in self.stock_codes:
            data = self.get_nvesto_data(stock_code, date_str, date_str)
            print(data)


    def get_nvesto_cookie(self):
        cookie = open(self.cookie_string_file).read(10000).strip()
        return cookie


    def crawl_nvesto_page_info(self, page_url):
        cookie = self.get_nvesto_cookie()
        pycurl_options = [
            (pycurl.COOKIE, cookie),
        ]
        result = self.get_html(page_url, pycurl_options)

        # 由 html 取得 MajorForce_JS_VARS 內容
        search = re.search('(MajorForce_JS_VARS=({.*?});)', result)
        major_force_string = search.group(1)
        json_string = search.group(2)
        if (0 == len(json_string)):
            raise CrawlerException('找不到 MajorForce_JS_VARS 內容')

        # 將 MajorForce_JS_VARS 內容寫入 get_secret_token/input.js
        mf_file = 'get_secret_token/input.js'
        f = open(mf_file, 'w')
        f.write(major_force_string)
        f.close()

        try:
            self.major_force_json = json.loads(json_string)
        except json.decoder.JSONDecodeError:
            raise CrawlerException('MajorForce_JS_VARS 內容無法轉換成 JSON 格式')


    def get_nvesto_data(self, stock_code, from_date, to_date):
        page_base_url = 'https://www.nvesto.com/tpe/{}/majorForce'.format(stock_code)
        page_full_url = """{}#!/fromdate/{}/todate/{}/view/detail""".format(page_base_url, from_date, to_date)
        self.crawl_nvesto_page_info(page_full_url)

        major_force_json = self.major_force_json

        # get csrf
        try:
            csrf = major_force_json['data']['csrf']
        except KeyError:
            raise CrawlerException('MajorForce_JS_VARS 中找不到 csrf')

        secret_token = self.generate_secret_token(from_date, to_date)
        if (0 == len(secret_token)):
            raise CrawlerException('產生 secretToken 失敗')

        data = json.dumps({
            "fromdate": from_date,
            "todate": to_date,
            "view": "detail",
            "csrf": csrf,
            "secretToken": secret_token
        })
        print(data)
        headers = [
            'Origin: https://www.nvesto.com',
            'X-Requested-With: XMLHttpRequest',
            #'Content-Type: application/x-www-form-urlencoded; charset=UTF-8',
        ]
        pycurl_options = [
            (pycurl.POST, 1),
            (pycurl.POSTFIELDS, data),
            (pycurl.COOKIE, self.get_nvesto_cookie()),
            (pycurl.REFERER, '{}'.format(page_base_url)),
            (pycurl.USERAGENT, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'),
            (pycurl.HTTPHEADER, headers)
        ]
        ajax_data_url = 'https://www.nvesto.com{}'.format(major_force_json['dataUrl'])
        result = self.get_html(ajax_data_url, pycurl_options)
        print(result)
        sys.exit(0)

    def generate_secret_token(self, from_date, to_date):
        # 產生 secretToken
        # 必須先將 MajorForce_JS_VARS={...} 寫入 get_secret_token/input.js
        secret_token_url = """http://localhost:8000/secret.html#!/fromdate/{}/todate/{}/view/detail""".format(from_date, to_date)
        driver = self.get_chrome_driver()
        driver.get(secret_token_url)
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "secret"))
        )
        span = driver.find_element_by_id('secret')
        secret_token = span.text
        return secret_token

    def get_html(self, url, pycurl_options=[]):
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
        return body.decode('utf-8')

    def set_chrome_driver(self):
        self.service = webdriver.chrome.service.Service(os.path.abspath("chromedriver"))
        self.service.start()

        chrome_options = Options()  
        #chrome_options.add_argument("--headless")  
        chrome_options.add_argument("--start-maximized")
        chrome_options.binary_location = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'
        #driver = webdriver.Chrome(executable_path=os.path.abspath("chromedriver"), chrome_options=chrome_options)
        self.chrome_driver = webdriver.Remote(self.service.service_url, desired_capabilities=chrome_options.to_capabilities())

    def unset_chrome_driver(self):
        self.chrome_driver.close()

    def get_chrome_driver(self):
        return self.chrome_driver

    def get_cookie_dicts_from_file(self):
        cookie_string = open('cookie_string.txt').read()
        cookie = SimpleCookie()
        cookie.load(cookie_string)
        cookie_dicts = []
        for key, morsel in cookie.items():
            cookie_dicts.append({'name': key, 'value': morsel.value})
        return cookie_dicts

    def get_cookie_dicts(self):
        cookie_dicts = [
            {'name': 'SERVERID', 'value': 'warrior'},
            {'name': '__utmt', 'value': '1'},
            {'name': 'PHPSESSID', 'value': 'tk30s099ofc26nh1kq0203ar44'},
            {'name': '2bd8f60281051886518bc3f76c3bc3b8', 'value': '098b9316db5a7deecbd1329a56f5f88abff02629a%3A4%3A%7Bi%3A0%3Bs%3A5%3A%2250851%22%3Bi%3A1%3Bs%3A2%3A%22yo%22%3Bi%3A2%3Bi%3A2592000%3Bi%3A3%3Ba%3A1%3A%7Bs%3A13%3A%22lastLoginTime%22%3Bi%3A1504716977%3B%7D%7D'},
            {'name': '__utma', 'value': '145157483.4805204.1504714760.1504719510.1504725217.3'},
            {'name': '__utmb', 'value': '145157483.4.10.1504725217'},
            {'name': '__utmc', 'value': '145157483'},
            {'name': '__utmz', 'value': '145157483.1504714760.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)'},
        ]
        return cookie_dicts

    def get_page(self):
        cookie_dicts = self.get_cookie_dicts()
        print(cookie_dicts)
        driver = self.get_chrome_driver()
        for cookie_dict in cookie_dicts:
            driver.add_cookie(cookie_dict)
        driver.get("https://www.nvesto.com/")
        print(driver.get_cookies())

    def login_nvesto(self):
        driver = self.get_chrome_driver()
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
    #crawler.get_page()
    #sys.exit(0)

    # If back flag is on, crawl till 2014/2/11, else crawl one day
    if args.back or args.check:
        last_day = first_day - timedelta(365) if args.back else first_day - timedelta(10)
        max_error = 5
        error_times = 0

        while error_times < max_error and first_day >= last_day:
            try:
                crawler.get_data((first_day.year, first_day.month, first_day.day))
                error_times = 0
            except Exception as e:
                date_str = first_day.strftime('%Y/%m/%d')
                logging.error('Crawl raise error {}: {}'.format(date_str, e))
                error_times += 1
                continue
            finally:
                first_day -= timedelta(1)
    else:
        crawler.get_data((first_day.year, first_day.month, first_day.day))


class CrawlerException(Exception):
    pass


if __name__ == '__main__':
    main()
