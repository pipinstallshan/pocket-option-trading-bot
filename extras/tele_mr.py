import re
import time
import pytz
import json
import base64
import random
import decimal
import hashlib
import numpy as np
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TelegramBot:
    driver = None
    group_ids = set()
    group_signals = []
    
    def __init__(self):
        self.load_web_driver()
        self.wait = WebDriverWait(self.driver, 10)
        print("Connect to VPN!")
        time.sleep(30)
        print("VPN connect timeout!")
        
    def load_web_driver(self):
        options = Options()
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_argument(r'--user-data-dir=/Users/hp/Library/Application Support/Google/Chrome/Profile 1')
        service = Service(executable_path=r'./bin/chromedriver.exe')
        self.driver = webdriver.Chrome(options=options, service=service)
        url = "https://web.telegram.org"
        self.driver.get(url)
    
    def click_on_group(self, group_to_target):
        self.wait.until(EC.presence_of_element_located((By.XPATH, f'//div[@class="ListItem Chat chat-item-clickable group has-ripple"]//h3[contains(@class, "fullName")][contains(text(), "{group_to_target}")]/ancestor::a')))    
        group_name = self.driver.find_element(By.XPATH, f'//div[@class="ListItem Chat chat-item-clickable group has-ripple"]//h3[contains(@class, "fullName")][contains(text(), "{group_to_target}")]/ancestor::a')
        group_name.click()
        
    def get_messages(self):
        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, '(//div[contains(@id, "message")])[position() = last()]//div[@class="text-content clearfix with-meta"]')))
            message = self.driver.find_element(By.XPATH, '(//div[contains(@id, "message")])[position() = last()]//div[@class="text-content clearfix with-meta"]')
            html_content = message.get_attribute('innerHTML')
            soup = BeautifulSoup(html_content, 'html.parser')
            try:
                texts = soup.findAll(text=True)
                final_text = ""
                for text in texts:
                    if text.strip():
                        final_text += text.strip() + " "
                message_id = self.driver.find_element(By.XPATH, '(//div[contains(@id, "message")])[position() = last()]').get_attribute('id')
                
                if message_id not in self.group_ids:
                    self.group_ids.add(message_id)
                    match = re.search(r'(?P<currencyPair>[A-Z]{3}/[A-Z]{3})\s*;\s*(?P<action>UP|DOWN)\s*EXPIRY TIME:\s*(?P<expiryTime>\d+\s*\w+)\s*Click to open broker\s*\d+\s*(?P<signalReceived>\d+:\d+)', final_text)
                    if match:
                        trade_id = hashlib.sha256(",".join([match.group("currencyPair"), match.group("action"), match.group("expiryTime"), match.group("signalReceived")]).encode()).hexdigest()
                        trade_info = {
                            "tradeId": trade_id,
                            "messageId": message_id,
                            "currencyPair": match.group("currencyPair"),
                            "action": match.group("action"),
                            "expiryTime": match.group("expiryTime"),
                            "signalReceived": match.group("signalReceived")
                        }
                        print("Signal : ", trade_info)
                        self.group_signals.append(trade_info)
                        self.save2json()
            except Exception as e:
                print("Error while getting text from message: ", e)
        except Exception as e:
            print("Error while getting message: ", e)
    
    def save2json(self):
        with open("./jsons/signals_mr.json", 'w', encoding='utf-8') as file:
            json.dump(self.group_signals, file, indent=4, ensure_ascii=False)
    
    def main(self):
        group_to_target = "MagicRoom (VIP)"
        try:
            self.click_on_group(group_to_target)
            print("Group enter successful")
        except Exception as e:
            print("Error while opening group: ", e)
            exit()
        
        while True:
            time.sleep(1)
            self.get_messages()
            
if __name__ == '__main__':
    bot = TelegramBot()
    bot.main()