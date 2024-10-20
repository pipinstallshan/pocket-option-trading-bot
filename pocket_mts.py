import os
import time
import pytz
import json
import math
import yaml
import random
import logging
from pathlib import Path
from selenium import webdriver
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from logging.handlers import RotatingFileHandler
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

TRADE_EQUITY_PERCENT = config['TRADE_EQUITY_PERCENT']

handler = RotatingFileHandler(
    './logs/POCKET_MAGIC_TRADER_SIGNALS.log', 
    maxBytes=1 * 1024 * 1024 * 1024,
    backupCount=0 
)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

class TradingBot:
    BASE_URL = 'https://pocketoption.com'
    TRADE_RECORD = 0
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
        os.system('cls')
        
    def load_web_driver(self):
        options = Options()
        options.add_argument('--headless=new')
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_argument(f'--user-data-dir={os.path.join(str(Path.home()), "AppData", "Local", "Google", "Chrome", "User Data", "Pocket")}')
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(options=options, service=service)
        self.driver.maximize_window()
        url = f'{self.BASE_URL}/en/cabinet/demo-quick-high-low/'
        self.driver.get(url)
    
    def change_currency(self):
        try:
            current_day = datetime.now(pytz.utc).weekday()
            is_weekend = current_day >= 5
            current_symbol = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'current-symbol')))
            current_symbol.click()
            time.sleep(2)
            if is_weekend:
                currency = self.driver.find_element(By.XPATH, f"//li[contains(., '{self.CURRENCY}')]//span[@class='alist__label'][contains(text(), 'OTC')]/parent::a")
            else:
                currency = self.driver.find_element(By.XPATH, f"//li[contains(., '{self.CURRENCY}')]//span[@class='alist__label'][not(contains(text(), 'OTC'))]/parent::a")
            if currency:
                currency_text = currency.text.strip()
                if currency_text != self.CURRENCY:
                    time.sleep(2)
                    currency.location_once_scrolled_into_view
                    time.sleep(2)
                    currency.click()
            time.sleep(2)
            self.driver.refresh()
            return True
        except TimeoutException as e:
            logging.error(f"Timeout during currency change: {e}")
            return False
        except Exception as e:
            logging.exception(f"Error during currency change: {e}")
            time.sleep(2)
            self.driver.refresh()
            return False
    
    def check_trade_result(self):
        try:
            closed_tab = self.driver.find_element(by=By.CSS_SELECTOR, value='#bar-chart > div > div > div.right-widget-container > div > div.widget-slot__header > div.divider > ul > li:nth-child(2) > a')
            closed_tab_parent = closed_tab.find_element(by=By.XPATH, value='..')
            if closed_tab_parent.get_attribute('class') == '':
                closed_tab_parent.click()
        except:
            pass
        
        previous_trade_currencies = self.driver.find_elements(by=By.CLASS_NAME, value='deals-list__item')
        while True:
            closed_trades_currencies = self.driver.find_elements(by=By.CLASS_NAME, value='deals-list__item')
            if len(closed_trades_currencies) > len(previous_trade_currencies):
                if closed_trades_currencies:
                    last_split = closed_trades_currencies[0].text.split('\n')
                try:
                    # amount = self.driver.find_element(by=By.CSS_SELECTOR, value='#put-call-buttons-chart-1 > div > div.blocks-wrap > div.block.block--bet-amount > div.block__control.control > div.control__value.value.value--several-items > div > input[type=text]')
                    # amount_value = int(amount.get_attribute('value'))
                    if '$0' not in last_split[4]:                                             # Win
                        print(f"🏆 Trade Win : {last_split[4]}\n")
                        return True
                    elif '$0' not in last_split[3]:                                           # Draw
                        print(f"🆗 Trade Draw : {last_split[3]}\n")
                        return True
                    else:                                                                       # Lose
                        print(f"❌ Trade Lost : {last_split[4]}\n")
                        return False
                except Exception as e:
                    print(f"Exception func check_trade_result : {e}")
                break
    
    def set_trade_amount(self, trade_amount):
        amount_element = self.driver.find_element(by=By.CSS_SELECTOR, value='#put-call-buttons-chart-1 > div > div.blocks-wrap > div.block.block--bet-amount > div.block__control.control > div.control__value.value.value--several-items > div > input[type=text]')
        amount_element.clear()
        amount_element.send_keys("0")
        time.sleep(random.choice([0.8, 0.9, 1.0, 1.1]))
        amount_element.send_keys(str(trade_amount))
        print(f"Trade amount set to ${trade_amount}")
        return
    
    def execute_trade(self, trade_info):
        if self.TRADE_RECORD == 0:
            start_time = time.time()
            while True:
                time.sleep(0.3)
                utc_now = datetime.utcnow()
                utc_minus_3 = utc_now - timedelta(hours=3)
                print(f"⏳ Waiting for execution [ CURRENT TIME : {utc_minus_3.strftime('%H:%M:%S')} ] [ INITIAL TRADE ] : ", trade_info, "\n")
                try:
                    if utc_minus_3.strftime('%H:%M') == trade_info['tradeExecution']:
                        total_balance = int(float((self.driver.find_element(By.XPATH, '//header//span[contains(@class, "js-balance")]').text).strip()))
                        twoPercent = max(1, math.floor(total_balance * float(f"{0.0}{TRADE_EQUITY_PERCENT}")))
                        self.set_trade_amount(twoPercent)
                        self.ACTION = trade_info['action'].lower()
                        break
                    elif datetime.strptime(utc_minus_3.strftime('%H:%M'), "%H:%M") > datetime.strptime(trade_info['tradeExecution'], "%H:%M"):
                        print(f"⏳ Execution Time Exceeded --> GALE 1 [ CURRENT TIME : {utc_minus_3.strftime('%H:%M:%S')} ] [ INITIAL TRADE ] : ", trade_info, "\n")
                        self.TRADE_RECORD = 1
                        self.execute_trade(trade_info)
                        
                    elapsed_time = time.time() - start_time
                    if elapsed_time > 300:
                        return
                    
                except NoSuchElementException as e:
                    logging.error(f"Element not found func execute_trade while loop Initial: {e}")
                except TimeoutException as e:
                    logging.error(f"Timeout during trade execution func execute_trade while loop Initial: {e}")
                except Exception as e:
                    logging.exception(f"Error during trade execution func execute_trade while loop Initial: {e}")
                
            try:
                if self.ACTION == "buy" or self.ACTION == "call":
                    self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-call')))
                    buy_button = self.driver.find_element(By.CLASS_NAME, 'btn-call')
                    buy_button.click()
                    print(f"📈 Executed Buy at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                elif self.ACTION == "sell" or self.ACTION == "put":
                    self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-put')))
                    sell_button = self.driver.find_element(By.CLASS_NAME, 'btn-put')
                    sell_button.click()
                    print(f"📉 Executed Sell at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                print("Trade Executed : ", trade_info, "\n")
                
                amount = self.driver.find_element(by=By.CSS_SELECTOR, value='#put-call-buttons-chart-1 > div > div.blocks-wrap > div.block.block--bet-amount > div.block__control.control > div.control__value.value.value--several-items > div > input[type=text]')
                bool_check_result = self.check_trade_result()
                if bool_check_result == True:
                    self.TRADE_RECORD = 0
                    return
                else:
                    self.TRADE_RECORD = 1
                    amount.click()
                    time.sleep(random.choice([0.8, 0.9, 1.0, 1.1]))
                    self.driver.find_element(By.XPATH, '(//div[@class="multiply__btn"])[position() = last()-1]').click()
                    time.sleep(random.choice([0.8, 0.9, 1.0, 1.1]))
                    self.execute_trade(trade_info)
                
            except NoSuchElementException as e:
                logging.error(f"Element not found func execute_trade Initial: {e}")
            except TimeoutException as e:
                logging.error(f"Timeout during trade execution func execute_trade Initial: {e}")
            except Exception as e:
                logging.exception(f"Error during trade execution func execute_trade Initial: {e}")
                
        elif self.TRADE_RECORD == 1:
            start_time = time.time()
            while True:
                time.sleep(0.2)
                utc_now = datetime.utcnow()
                utc_minus_3 = utc_now - timedelta(hours=3)
                print(f"⏳ Waiting for execution [ CURRENT TIME : {utc_minus_3.strftime('%H:%M:%S')} ] [ GALE 1 ] : ", trade_info, "\n")
                try:
                    if utc_minus_3.strftime('%H:%M') == trade_info['galeOne']:
                        self.ACTION = trade_info['action'].lower()
                        break
                    elif datetime.strptime(utc_minus_3.strftime('%H:%M'), "%H:%M") > datetime.strptime(trade_info['galeOne'], "%H:%M"):
                        print(f"⏳ Execution Time Exceeded --> GALE 2 [ CURRENT TIME : {utc_minus_3.strftime('%H:%M:%S')} ] [ GALE 1 ] : ", trade_info, "\n")
                        self.TRADE_RECORD = 2
                        self.execute_trade(trade_info)

                    elapsed_time = time.time() - start_time
                    if elapsed_time > 300:
                        return
                    
                except NoSuchElementException as e:
                    logging.error(f"Element not found func execute_trade while loop GALE 1: {e}")
                except TimeoutException as e:
                    logging.error(f"Timeout during trade execution func execute_trade while loop GALE 1: {e}")
                except Exception as e:
                    logging.exception(f"Error during trade execution func execute_trade while loop GALE 1: {e}")
                
            try:
                if self.ACTION == "buy" or self.ACTION == "call":
                    self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-call')))
                    buy_button = self.driver.find_element(By.CLASS_NAME, 'btn-call')
                    buy_button.click()
                    print(f"📈 Executed Buy at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                elif self.ACTION == "sell" or self.ACTION == "put":
                    self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-put')))
                    sell_button = self.driver.find_element(By.CLASS_NAME, 'btn-put')
                    sell_button.click()
                    print(f"📉 Executed Sell at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                print("Trade Executed : ", trade_info, "\n")
                
                amount = self.driver.find_element(by=By.CSS_SELECTOR, value='#put-call-buttons-chart-1 > div > div.blocks-wrap > div.block.block--bet-amount > div.block__control.control > div.control__value.value.value--several-items > div > input[type=text]')
                bool_check_result = self.check_trade_result()
                if bool_check_result == True:
                    self.TRADE_RECORD = 0
                    amount = self.driver.find_element(by=By.CSS_SELECTOR, value='#put-call-buttons-chart-1 > div > div.blocks-wrap > div.block.block--bet-amount > div.block__control.control > div.control__value.value.value--several-items > div > input[type=text]')
                    amount.click()
                    time.sleep(random.choice([0.6, 0.7, 0.8, 0.9, 1.0, 1.1]))
                    self.driver.find_element(By.XPATH, '(//div[@class="multiply__btn"])[position() = last()]').click()
                    time.sleep(2)
                    return
                else:
                    self.TRADE_RECORD = 2
                    amount.click()
                    time.sleep(random.choice([0.6, 0.7, 0.8, 0.9, 1.0, 1.1]))
                    self.driver.find_element(By.XPATH, '(//div[@class="multiply__btn"])[position() = last()-1]').click()
                    time.sleep(2)
                    self.execute_trade(trade_info)
                        
            except NoSuchElementException as e:
                logging.error(f"Element not found func execute_trade [ Gale 1 ] : {e}")
            except TimeoutException as e:
                logging.error(f"Timeout during trade execution func execute_trade [ Gale 1 ] : {e}")
            except Exception as e:
                logging.exception(f"Error during trade execution func execute_trade [ Gale 1 ] : {e}")
                
        elif self.TRADE_RECORD == 2:
            start_time = time.time()
            while True:
                time.sleep(0.2)
                utc_now = datetime.utcnow()
                utc_minus_3 = utc_now - timedelta(hours=3)
                print(f"⏳ Waiting for execution [ CURRENT TIME : {utc_minus_3.strftime('%H:%M:%S')} ] [ GALE 2 ] : ", trade_info, "\n")
                try:
                    if utc_minus_3.strftime('%H:%M') == trade_info['galeTwo']:
                        self.ACTION = trade_info['action'].lower()
                        break
                    elif datetime.strptime(utc_minus_3.strftime('%H:%M'), "%H:%M") > datetime.strptime(trade_info['galeTwo'], "%H:%M"):
                        print(f"⏳ Execution Time Exceeded --> Returning [ CURRENT TIME : {utc_minus_3.strftime('%H:%M:%S')} ] [ GALE 2 ] : ", trade_info, "\n")
                        self.TRADE_RECORD = 0
                        return

                    elapsed_time = time.time() - start_time
                    if elapsed_time > 300:
                        return
                except NoSuchElementException as e:
                    logging.error(f"Element not found func execute_trade while loop GALE 2: {e}")
                except TimeoutException as e:
                    logging.error(f"Timeout during trade execution func execute_trade while loop GALE 2: {e}")
                except Exception as e:
                    logging.exception(f"Error during trade execution func execute_trade while loop GALE 2: {e}")
                
            try:
                if self.ACTION == "buy" or self.ACTION == "call":
                    self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-call')))
                    buy_button = self.driver.find_element(By.CLASS_NAME, 'btn-call')
                    buy_button.click()
                    print(f"📈 Executed Buy at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                elif self.ACTION == "sell" or self.ACTION == "put":
                    self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-put')))
                    sell_button = self.driver.find_element(By.CLASS_NAME, 'btn-put')
                    sell_button.click()
                    print(f"📉 Executed Sell at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                print("Trade Executed : ", trade_info, "\n")
                
                amount = self.driver.find_element(by=By.CSS_SELECTOR, value='#put-call-buttons-chart-1 > div > div.blocks-wrap > div.block.block--bet-amount > div.block__control.control > div.control__value.value.value--several-items > div > input[type=text]')
                bool_check_result = self.check_trade_result()
                if bool_check_result == True:
                    self.TRADE_RECORD = 0
                    amount.click()
                    time.sleep(random.choice([0.6, 0.7, 0.8, 0.9, 1.0, 1.1]))
                    self.driver.find_element(By.XPATH, '(//div[@class="multiply__btn"])[position() = last()]').click()
                    time.sleep(2)
                    self.driver.find_element(By.XPATH, '(//div[@class="multiply__btn"])[position() = last()]').click()
                    time.sleep(2)
                    return
                else:
                    self.TRADE_RECORD = 0
                    amount.click()
                    time.sleep(random.choice([0.6, 0.7, 0.8, 0.9, 1.0, 1.1]))
                    self.driver.find_element(By.XPATH, '(//div[@class="multiply__btn"])[position() = last()]').click()
                    time.sleep(2)
                    self.driver.find_element(By.XPATH, '(//div[@class="multiply__btn"])[position() = last()]').click()
                    time.sleep(2)
                    return
                        
            except NoSuchElementException as e:
                logging.error(f"Element not found func execute_trade [ Gale 2 ] : {e}")
            except TimeoutException as e:
                logging.error(f"Timeout during trade execution func execute_trade [ Gale 2 ] : {e}")
            except Exception as e:
                logging.exception(f"Error during trade execution func execute_trade [ Gale 2 ] : {e}")

    def execute_trade_from_signal(self, trade_info):
        self.CURRENCY = trade_info["currencyPair"]
        local_trade_time = trade_info["localTime"]
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'current-symbol')))
        current_symbol = self.driver.find_element(By.CLASS_NAME, 'current-symbol')
        
        current_time = datetime.now().strftime('%H:%M')
        one_minute_before_trade_time = (current_time.split(":")[0] + ":") + (("0" + str((int(current_time.split(":")[1])+1))) if len(str((int(current_time.split(":")[1])+1))) == 1 else str((int(current_time.split(":")[1])+1)))
        if current_time == local_trade_time or current_time == one_minute_before_trade_time:
            print("Signal Recieved : ", trade_info, "\n")
            
            if self.CURRENCY == current_symbol.text:
                time.sleep(5)
                print(f"Same currency : {self.CURRENCY}\n")
                self.execute_trade(trade_info)
                
            if self.CURRENCY != current_symbol.text:
                print(f"Changing currency : {current_symbol.text} --> {self.CURRENCY}\n")
                state_currency = self.change_currency()
                if state_currency == True:
                    print(f"Currency changed : {self.CURRENCY}\n")
                    time.sleep(5)
                    self.execute_trade(trade_info)
                else:
                    print(f"Currency not found : {self.CURRENCY}\n")
                    time.sleep(5)
                    return
    
    def restart_driver(self):
        self.driver.quit()
        self.load_web_driver()
        self.wait = WebDriverWait(self.driver, 10)
    
    def main(self):
        print("POCKET BOT LIVE...\n")
        start_time = time.time()
        while True:
            time.sleep(random.randint(1,2))
            try:
                with open('./jsons/signals_mts.json', 'r', encoding='utf-8') as f:
                    trade_data = json.load(f)
                    last_trade = trade_data[-1]
                    trade_id = last_trade['tradeId']
                    if trade_id not in bot.TRADES_EXECUTED_ID:
                        bot.TRADES_EXECUTED_ID.add(trade_id)
                        bot.execute_trade_from_signal(last_trade)
                        
                if time.time() - start_time > random.randint(700, 900):
                    print(f"{time.time()} Restarting driver...")
                    self.restart_driver()
                    start_time = time.time()
                    os.system('cls')
                    print("POCKET BOT LIVE...\n")
                    
            except NoSuchElementException as e:
                logging.error(f"Element not found main : {e}")
                continue
            except TimeoutException as e:
                logging.error(f"Timeout during trade execution main : {e}")
                continue
            except Exception as e:
                logging.exception(f"Error during trade execution main : {e}")
                continue
            
if __name__ == '__main__':
    bot = TradingBot()
    bot.main()