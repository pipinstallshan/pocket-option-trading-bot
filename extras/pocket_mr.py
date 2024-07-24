import time
import pytz
import json
import base64
import random
import decimal
import logging
import numpy as np
from selenium import webdriver
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logging.basicConfig(filename='./logs/POCKET_MAGIC_ROOM.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TradingBot:
    BASE_URL = 'https://pocketoption.com'
    CURRENCY = None
    ACTION = None
    wait = None
    driver = None
    TRADES_EXECUTED_ID = set()

    def __init__(self):
        self.load_web_driver()
        self.wait = WebDriverWait(self.driver, 10)
        time.sleep(5)
        print("Page load timeout")
        
    def load_web_driver(self):
        options = Options()
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_argument(r'--user-data-dir=/Users/hp/Library/Application Support/Google/Chrome/Pocket Option MR')
        service = Service(executable_path=r'./bin/chromedriver.exe')
        self.driver = webdriver.Chrome(options=options, service=service)
        url = f'{self.BASE_URL}/en/cabinet/demo-quick-high-low/'
        self.driver.get(url)

    def change_currency(self):
        try:
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'current-symbol')))
            current_symbol = self.driver.find_element(by=By.CLASS_NAME, value='current-symbol')
            current_symbol.click()
            currency = self.driver.find_element(By.XPATH, f"//li[contains(., '{self.CURRENCY}')]//span[@class='js-tour-asset-label alist__label'][not(contains(text(), 'OTC'))]")
            if currency:
                currency_text = currency.text.strip()
                if currency_text != self.CURRENCY:
                    currency.location_once_scrolled_into_view
                    time.sleep(1)
                    currency.click()
            time.sleep(2)
            self.driver.refresh()
        except TimeoutException as e:
            logging.error(f"Timeout during currency change: {e}")
        except Exception as e:
            logging.exception(f"Error during currency change: {e}")

    def execute_trade(self):
        try:
            if self.ACTION == "buy" or self.ACTION == "call":
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-call')))
                buy_button = self.driver.find_element(By.CLASS_NAME, 'btn-call')
                buy_button.click()
                logging.info(f"Executed Buy at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            elif self.ACTION == "sell" or self.ACTION == "put":
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-put')))
                sell_button = self.driver.find_element(By.CLASS_NAME, 'btn-put')
                sell_button.click()
                logging.info(f"Executed Sell at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except NoSuchElementException as e:
            logging.error(f"Element not found: {e}")
        except TimeoutException as e:
            logging.error(f"Timeout during trade execution: {e}")
        except Exception as e:
            logging.exception(f"Error during trade execution: {e}")

    def execute_trade_from_signal(self, trade_info):
        self.CURRENCY = trade_info["currencyPair"]
        self.change_currency()
        time.sleep(5)
        
        self.ACTION = trade_info["action"].lower()
        self.execute_trade()

if __name__ == '__main__':
    bot = TradingBot()
    while True:
        try:
            with open('./jsons/signals_mr.json', 'r', encoding='utf-8') as f:
                trade_data = json.load(f)
                for trade_obj in trade_data:
                    trade_id = trade_obj['tradeId']
                    if trade_id not in bot.TRADES_EXECUTED_ID:
                        bot.TRADES_EXECUTED_ID.add(trade_id)
                        print("\nTrade executed : ", trade_obj)
                        bot.execute_trade_from_signal(trade_obj)
        except:
            continue