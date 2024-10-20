import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


class LoginTelegram:
    driver = None
    group_ids = set()
    group_signals = []
    
    def __init__(self):
        self.load_web_driver()
        self.wait = WebDriverWait(self.driver, 10)

    def load_web_driver(self):
        options = Options()
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_argument(f'--user-data-dir={os.path.join(str(Path.home()), "AppData", "Local", "Google", "Chrome", "User Data", "Telegram")}')
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(options=options, service=service)
        self.driver.maximize_window()
        url = "https://web.telegram.org/a/"
        self.driver.get(url)
    
    def main(self):
        os.system("cls")
        print("\nInstructions:\n1. Login to Telegram.\n2. Once you have logged in close the chrome instance.\nP.S: Make sure you login through this link ONLY: https://web.telegram.org/a/")
        while True:
            ____ = []
            
if __name__ == '__main__':
    bot = LoginTelegram()
    bot.main()