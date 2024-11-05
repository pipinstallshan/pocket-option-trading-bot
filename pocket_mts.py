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
TRADING_ACCOUNT = config['ACCOUNT']

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
    CURRENT_TRADE_AMOUNT = ""
    
    def log_and_print(self, message):
        logger.info(message)
        print(message)
    
    def __init__(self):
        self.load_web_driver()
        self.wait = WebDriverWait(self.driver, 10)
        time.sleep(5)
        self.log_and_print("Page load timeout")
        os.system('cls')
        
    def load_web_driver(self):
        options = Options()
        # options.add_argument('--headless=new')
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
            time.sleep(random.choice([1.5, 1.8, 1.6, 1.7]))
            if is_weekend:
                currency = self.driver.find_element(By.XPATH, f"//li[contains(., '{self.CURRENCY}')]//span[@class='alist__label'][contains(text(), 'OTC')]/parent::a")
            else:
                currency = self.driver.find_element(By.XPATH, f"//li[contains(., '{self.CURRENCY}')]//span[@class='alist__label'][not(contains(text(), 'OTC'))]/parent::a")
            if currency:
                currency_text = currency.text.strip()
                if currency_text != self.CURRENCY:
                    time.sleep(random.choice([1.5, 1.8, 1.6, 1.7]))
                    currency.location_once_scrolled_into_view
                    time.sleep(random.choice([1.5, 1.8, 1.6, 1.7]))
                    currency.click()
                    time.sleep(random.choice([1.5, 1.8, 1.6, 1.7]))
                    
            self.driver.refresh()
            time.sleep(random.choice([2.5, 2.8, 2.6, 2.7]))
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
                    if '$0' not in last_split[4]:                                             # Win
                        self.log_and_print(f"🏆 Trade Win : {last_split[4]}\n")
                        return True
                    elif '$0' not in last_split[3]:                                           # Draw
                        self.log_and_print(f"🆗 Trade Draw : {last_split[3]}\n")
                        return True
                    else:                                                                       # Lose
                        self.log_and_print(f"❌ Trade Lost : {last_split[4]}\n")
                        return False
                except Exception as e:
                    logging.error(f"Exception func check_trade_result : {e}")
                break
    
    def get_balance(self):
        return int(float(self.driver.find_element(By.XPATH, '//header//span[contains(@class, "js-balance")]').text.replace(",", "").strip()))
    
    def set_trade_amount(self, trade_amount):
        self.driver.find_element(By.CSS_SELECTOR, '#put-call-buttons-chart-1 > div > div.blocks-wrap > div.block.block--bet-amount > div.block__control.control > div.control__value.value.value--several-items > div > input[type=text]').click()
        time.sleep(random.choice([0.5, 0.4, 0.3, 0.6]))
        
        for __ in range(0, 5):
            self.driver.find_element(By.XPATH, '//div[@class="virtual-keyboard__col"][position() = last()]').click()
        
        for digit in str(trade_amount):
            time.sleep(random.choice([0.1, 0.2, 0.3]))
            self.driver.find_element(By.XPATH, f'//div[@class="virtual-keyboard__col"]//div[@class="virtual-keyboard__input"][contains(text(), "{digit}")]').click()
        
        time.sleep(random.choice([0.9, 0.8, 0.6, 0.7]))
        self.log_and_print(f"💲 Trade amount set to ${str(trade_amount).strip()}\n")
        return trade_amount
    
    def wait_until_trade_time(self, trade_time):
        start_time = time.time()
        while True:
            time.sleep(0.2)
            current_time = (datetime.utcnow() - timedelta(hours=3)).strftime('%H:%M')
            self.log_and_print(f"⏳ Waiting for execution [CURRENT TIME: {current_time}] [TARGET TIME: {trade_time}]\n")
            
            if current_time == trade_time:
                return True
            elif datetime.strptime(current_time, "%H:%M") > datetime.strptime(trade_time, "%H:%M"):
                return False

            if time.time() - start_time > 300:
                return None

    def execute_trade_action(self):
        try:
            if self.ACTION == "buy" or "call":
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-call')))
                self.driver.find_element(By.CLASS_NAME, 'btn-call').click()
                self.log_and_print(f"📈 Executed Buy at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            elif self.ACTION == "sell" or "put":
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-put')))
                self.driver.find_element(By.CLASS_NAME, 'btn-put').click()
                self.log_and_print(f"📉 Executed Sell at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        except NoSuchElementException as e:
            logging.error(f"Element not found during trade execution: {e}")
        except TimeoutException as e:
            logging.error(f"Timeout during trade execution: {e}")

    def handle_trade_result(self):
        try:
            trade_success = self.check_trade_result()
            if trade_success:
                self.TRADE_RECORD = 0
                self.log_and_print("✅ Trade succeeded.\n")
                return True
            else:
                if self.TRADE_RECORD <= 2:
                    self.TRADE_RECORD += 1
                    self.log_and_print(f"❌ Trade failed. Attempting Martingale strategy - Record: {self.TRADE_RECORD}\n")
                    self.CURRENT_TRADE_AMOUNT = self.set_trade_amount(self.CURRENT_TRADE_AMOUNT * 2)
                return False
        
        except NoSuchElementException as e:
            logging.error(f"Element not found while handling trade result: {e}")
        except TimeoutException as e:
            logging.error(f"Timeout during handling trade result: {e}")
        return None

    def execute_trade(self, trade_info):
        time_field = ['tradeExecution', 'galeOne', 'galeTwo'][self.TRADE_RECORD]
        trade_time = trade_info.get(time_field)

        if trade_time:
            if self.wait_until_trade_time(trade_time) is not None:
                self.ACTION = trade_info['action'].lower()
                
                initial_trade_amount = max(1, math.floor(int(self.get_balance()) * float(f"{0.0}{TRADE_EQUITY_PERCENT}")))
                if self.TRADE_RECORD == 0:
                    self.CURRENT_TRADE_AMOUNT = self.set_trade_amount(initial_trade_amount)
                
                self.execute_trade_action()
                
                if self.handle_trade_result() is False:
                    if self.TRADE_RECORD <= 2:
                        self.log_and_print(f"🔄 Retrying trade with doubled amount. Attempt: {self.TRADE_RECORD}\n")
                        self.execute_trade(trade_info)
                    else:
                        self.log_and_print("⚠️ Maximum retries reached.\n")
                        self.TRADE_RECORD = 0
                        return
                else:
                    self.log_and_print(f"✅ Trade executed successfully and handled: {trade_info} \n")
                    
    def execute_trade_from_signal(self, trade_info):
        self.CURRENCY = trade_info["currencyPair"]
        local_trade_time = trade_info["localTime"]
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'current-symbol')))
        current_symbol = self.driver.find_element(By.CLASS_NAME, 'current-symbol')
        
        current_time = datetime.now().strftime('%H:%M')
        one_minute_before_trade_time = (current_time.split(":")[0] + ":") + (("0" + str((int(current_time.split(":")[1])+1))) if len(str((int(current_time.split(":")[1])+1))) == 1 else str((int(current_time.split(":")[1])+1)))
        if current_time == local_trade_time or current_time == one_minute_before_trade_time:
            self.log_and_print(f"Signal Recieved : {trade_info} \n")
            
            if self.CURRENCY == current_symbol.text:
                time.sleep(2)
                self.log_and_print(f"Same currency : {self.CURRENCY}\n")
                self.execute_trade(trade_info)
                return
                
            if self.CURRENCY != current_symbol.text:
                self.log_and_print(f"Changing currency : {current_symbol.text} --> {self.CURRENCY}\n")
                state_currency = self.change_currency()
                if state_currency == True:
                    self.log_and_print(f"Currency changed : {self.CURRENCY}\n")
                    time.sleep(2)
                    self.execute_trade(trade_info)
                    return
                else:
                    self.log_and_print(f"Currency not found : {self.CURRENCY}\n")
                    time.sleep(2)
                    return
    
    def switch_to_currencies(self):
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'current-symbol'))).click()
        time.sleep(random.choice([0.5, 0.8, 0.6, 0.7]))
        self.wait.until(EC.presence_of_element_located((By.XPATH, '//span[contains(text(), "Currencies")]'))).click()
        self.driver.refresh()
        time.sleep(random.choice([2.3, 2.2, 2.1, 2.0]))
        return
            
    def switch_real_or_demo(self):
        if TRADING_ACCOUNT.lower() == "demo":
            try:
                self.driver.find_element(By.XPATH, '//div[@class="right-block js-right-block"]//div[contains(text(), "QT Real")]')
                self.driver.get("https://pocketoption.com/en/cabinet/demo-quick-high-low/")
                time.sleep(random.choice([2.3, 2.2, 2.1, 2.0]))
                demo_identifier = self.wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="right-block js-right-block"]//div[contains(text(), "QT Demo")]')))
                if demo_identifier:
                    print(f"✅ Trading Account Switched to {TRADING_ACCOUNT} Successfully\n")
                    return
                else:
                    print(f"❌ Failed to switch to {TRADING_ACCOUNT} Trading Account \n")
                    exit(0)
            except:
                try:
                    demo_identifier = self.wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="right-block js-right-block"]//div[contains(text(), "QT Demo")]')))
                    if demo_identifier:
                        print(f"✅ Trading Account Switched to {TRADING_ACCOUNT} Successfully\n")
                        return
                except:
                    logging.error(f"❌ Failed to switch to {TRADING_ACCOUNT} Trading Account \n")
                    exit(0)
                    
        elif TRADING_ACCOUNT.lower() == "real":
            try:
                self.driver.find_element(By.XPATH, '//div[@class="right-block js-right-block"]//div[contains(text(), "QT Demo")]')
                self.driver.get("https://pocketoption.com/en/cabinet/")
                time.sleep(random.choice([2.3, 2.2, 2.1, 2.0]))
                real_identifier = self.wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="right-block js-right-block"]//div[contains(text(), "QT Real")]')))
                if real_identifier:
                    print(f"✅ Trading Account Switched to {TRADING_ACCOUNT} Successfully\n")
                    return
                else:
                    print(f"❌ Failed to switch to {TRADING_ACCOUNT} Trading Account \n")
                    exit(0)
            except:
                try:
                    real_identifier = self.wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="right-block js-right-block"]//div[contains(text(), "QT Real")]')))
                    if real_identifier:
                        print(f"✅ Trading Account Switched to {TRADING_ACCOUNT} Successfully\n")
                        return
                except:
                    logging.error(f"❌ Failed to switch to {TRADING_ACCOUNT} Trading Account \n")
                    exit(0)
        else:
            return
    
    def restart_driver(self):
        self.driver.execute_script("window.open('');")
        new_window = self.driver.window_handles[-1]
        self.driver.switch_to.window(new_window)
        original_window = self.driver.window_handles[0]
        self.driver.switch_to.window(original_window)
        self.driver.close()
        self.driver.switch_to.window(new_window)
        self.driver.maximize_window()
        url = f'{self.BASE_URL}/en/cabinet/demo-quick-high-low/'
        self.driver.get(url)
    
    def main(self):
        print("POCKET BOT LIVE...\n")
        start_time = time.time()
        self.switch_real_or_demo()
        self.switch_to_currencies()
        print(f"⏳ Waiting for Telegram Signals\n")
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
                    self.switch_real_or_demo()
                    self.switch_to_currencies()
                    
            except NoSuchElementException as e:
                logging.error(f"Element not found main : {e}")
                continue
            except TimeoutException as e:
                logging.error(f"Timeout during trade execution main : {e}")
                continue
            except json.JSONDecodeError as e:
                continue
            except Exception as e:
                logging.exception(f"Error during trade execution main : {e}")
                continue
            
if __name__ == '__main__':
    bot = TradingBot()
    bot.main()