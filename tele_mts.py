import os
import re
import time
import json
import yaml
import random
import hashlib
import logging
from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from logging.handlers import RotatingFileHandler
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

TELEGRAM_GROUP_NAME = config['TELEGRAM_GROUP_NAME']

handler = RotatingFileHandler(
    './logs/TELEGRAM_MAGIC_TRADER.log', 
    maxBytes=1 * 1024 * 1024 * 1024,
    backupCount=0,
    encoding='utf-8'
)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

class TelegramBot:
    driver = None
    group_ids = set()
    group_signals = []
    
    def log_and_print(self, message):
        logger.info(message)
        print(message)
    
    def __init__(self):
        self.load_web_driver()
        self.wait = WebDriverWait(self.driver, 60)
        time.sleep(3)

    def load_web_driver(self):
        options = Options()
        options.add_argument('--headless=new')
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_argument(f'--user-data-dir={os.path.join(str(Path.home()), "AppData", "Local", "Google", "Chrome", "User Data", "Telegram")}')
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(options=options, service=service)
        self.driver.maximize_window()
        url = "https://web.telegram.org/a"
        self.driver.get(url)
    
    def click_on_group(self, group_to_target):
        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, f'//h3[contains(text(), "{group_to_target}")]/ancestor::a')))    
            group_name = self.driver.find_element(By.XPATH, f'//h3[contains(text(), "{group_to_target}")]/ancestor::a')
            group_name.click()
        except Exception as e:
            logging.exception(f"Exception func click_on_group : {e}")
            self.click_on_group(group_to_target)
        
    def get_messages(self):
        try:
            try:
                scroll_down_button = self.driver.find_element(By.XPATH, '//div[@class="Transition"]/following-sibling::div//button[@aria-label="Go to bottom"]')
                if scroll_down_button:
                    scroll_down_button.click()
            except:
                pass
            
            message = self.driver.find_element(By.XPATH, '(//div[@class="bottom-marker"])[position() = last()]/parent::div[contains(@id, "message")]//div[contains(@class, "message-content-wrapper")]')
            html_content = message.get_attribute('innerHTML')
            soup = BeautifulSoup(html_content, 'html.parser')
            try:
                texts = soup.find_all(string=True)
                final_text = ""
                for text in texts:
                    if text.strip():
                        final_text += text.strip() + " "
                message_id = self.driver.find_element(By.XPATH, '(//div[@class="bottom-marker"])[position() = last()]/parent::div[contains(@id, "message")]//div[contains(@class, "message-content-wrapper")]/parent::div').get_attribute('data-message-id')
                    
                if message_id not in self.group_ids:
                    self.group_ids.add(message_id)
                    self.wait.until(EC.presence_of_element_located((By.XPATH, '(//span[@class="message-time"])[position() = last()]')))
                    local_time = self.driver.execute_script("""
                        const xpath = '(//span[@class="message-time"])[position() = last()]';
                        const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                        return result.singleNodeValue ? result.singleNodeValue.textContent.trim() : null;
                    """)
                    match = re.search(r'(?P<currencyPair>[A-Z]{3}/[A-Z]{3});(?P<tradeExecution>\d{2}:\d{2});(?P<action>PUT|CALL)\s*TIME TO (?P<galeOne>\d{2}:\d{2})\s*1st GALE —>TIME TO (?P<galeTwo>\d{2}:\d{2})\s*2nd GALE —TIME TO (?P<tradeExpiration>\d{2}:\d{2})', final_text) or re.search(r'(?P<currencyPair>[A-Z]{3}/[A-Z]{3});(?P<tradeExecution>\d{2}:\d{2});(?P<action>PUT|CALL)\s*TIME TO (?P<galeOne>\d{2}:\d{2})\s*1st GALE —>TIME TO (?P<galeTwo>\d{2}:\d{2})\s*2nd GALE — TIME TO (?P<tradeExpiration>\d{2}:\d{2})', final_text) or re.search(r'(?P<currencyPair>[A-Z]{3}/[A-Z]{3});(?P<tradeExecution>\d{2}:\d{2});(?P<action>PUT|CALL)\s*TIME TO (?P<galeOne>\d{2}:\d{2})\s*1st GALE —>TIME TO (?P<galeTwo>\d{2}:\d{2})\s*2nd GALE —>TIME TO (?P<tradeExpiration>\d{2}:\d{2})', final_text)
                    if match:
                        trade_id = hashlib.sha256(",".join([
                            match.group("currencyPair"),
                            match.group("action"),
                            match.group("galeOne"),
                            match.group("tradeExecution")
                        ]).encode()).hexdigest()
                        
                        trade_info = {
                            "tradeId": trade_id,
                            "messageId": message_id,
                            "currencyPair": match.group("currencyPair"),
                            "action": match.group("action"),
                            "tradeExecution": match.group("tradeExecution"),
                            "galeOne": match.group("galeOne"),
                            "galeTwo": match.group("galeTwo"),
                            "tradeExpiration": match.group("tradeExpiration"),
                            "localTime": local_time.replace("PM", "").replace("AM", "").strip()
                        }
                        self.log_and_print(f"\nSignal : {trade_info}")
                        logging.info(f"\nSignal : {trade_info}")
                        self.group_signals.append(trade_info)
                        self.save2json()
            except Exception as e:
                logging.exception(f"get_messages func: Error while getting text from message: {e}")
        except Exception as e:
            logging.exception(f"get_messages func: Error while getting message: {e}")

    def restart_driver(self):
        self.driver.execute_script("window.open('');")
        new_window = self.driver.window_handles[-1]
        self.driver.switch_to.window(new_window)
        original_window = self.driver.window_handles[0]
        self.driver.switch_to.window(original_window)
        self.driver.close()
        self.driver.switch_to.window(new_window)
        self.driver.maximize_window()
        url = "https://web.telegram.org/a"
        self.driver.get(url)
    
    def save2json(self):
        with open("./jsons/signals_mts.json", 'w', encoding='utf-8') as file:
            json.dump(self.group_signals, file, indent=4, ensure_ascii=False)
    
    def main(self):
        group_to_target = TELEGRAM_GROUP_NAME
        try:
            self.click_on_group(group_to_target)
            self.log_and_print(f"Group enter successful")
            os.system("cls")
            self.log_and_print("TELEGRAM BOT LIVE...\n")
        except Exception as e:
            logging.exception(f"main func: Error while opening group: {e}")
            exit()

        start_time = time.time()
        while True:
            time.sleep(random.randint(1,2))
            self.get_messages()
            
            # I use this code to restart so that the process could refresh if it got stuck somewhere
            # ***************************************************************************************
            
            time.sleep(1)
            if time.time() - start_time > random.randint(700, 900):
                self.log_and_print(f"\nRestarting driver...")
                self.restart_driver()
                try:
                    self.click_on_group(group_to_target)
                    self.log_and_print(f"Group re-enter successful")
                    os.system("cls")
                    self.log_and_print("TELEGRAM BOT LIVE...\n")
                except Exception as e:
                    self.log_and_print(f"Error while reopening group: {e}")
                    exit()
                start_time = time.time()
            
if __name__ == '__main__':
    bot = TelegramBot()
    bot.main()