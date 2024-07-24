# Pocket Option Magic Trader Signals Bot

This project is a Python-based bot that automates trading on the Pocket Option platform using signals from a Telegram group called "Magic Trader Signals". The bot automatically executes trades based on the signals received from the Telegram group, aiming to profit from the signals.

## Project Structure

The project consists of the following files:
- `main`: Runs the cronjob.
- `cronjob_pocket.py`: Runs a cronjob that checks for time intervals and starts the `pocket_mts.py` script for trading.
- `cronjob_tele.py`: Runs a cronjob that checks for time intervals and starts the `tele_mts.py` script for retrieving signals from Telegram.
- `pocket_mts.py`: Contains the core logic for the trading bot, including connecting to the Pocket Option website, executing trades based on signals, and managing trade results.
- `tele_mts.py`: Contains the logic for connecting to the Telegram group, extracting signals, and saving them to a JSON file.
- `jsons/signals_mts.json`: Stores the extracted signals from the Telegram group.
- `bin/chromedriver.exe`: The ChromeDriver executable for Selenium use the latest ChromeDriver.
- `logs/POCKET_MAGIC_TRADER_SIGNALS.log`: Log file for the Pocket Option bot.
- `logs/TELEGRAM_MAGIC_TRADER.log`: Log file for the Telegram bot.

## Requirements

### Python Version
- I have tested on Python 3.8.

### Dependencies
- The following Python packages are required:
  - `selenium`
  - `pytz==2023.3`

## Usage

This bot is provided for informational purposes only. It is not a financial advisor and should not be considered investment advice. Using this bot carries risk and may result in losses. You are responsible for your own trading decisions and should consult with a qualified financial professional before making any investment decisions.

##  Contribution

Contributions to this project are welcome! You can contribute by:

`Reporting issues`: If you encounter any bugs or issues, please report them on the GitHub issue tracker.<br></br>
`Submitting pull requests`: If you have any improvements or new features, feel free to submit a pull request.<br></br>
`Providing feedback`: Your feedback is valuable and helps improve the project.<br></br>

## License
[MIT](https://choosealicense.com/licenses/mit/)
