import os
import time
import pytz
import psutil
import subprocess
from datetime import datetime

morning_start = "07:00"
morning_end = "11:30"
afternoon_start = "16:00"
afternoon_end = "23:00"

pk_tz = pytz.timezone('Asia/Karachi')

def get_time_range(start, end):
    today = datetime.now(pk_tz).date()
    start_time = pk_tz.localize(datetime.strptime(f"{today} {start}", "%Y-%m-%d %H:%M"))
    end_time = pk_tz.localize(datetime.strptime(f"{today} {end}", "%Y-%m-%d %H:%M"))
    return start_time, end_time

def is_within_timeframe(start, end):
    now = datetime.now(pk_tz)
    return start <= now <= end

def terminate_chrome():
    for proc in psutil.process_iter(['pid', 'name']):
        if 'chrome' in proc.info['name']:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                pass

def terminate_script():
    current_pid = os.getpid()
    parent = psutil.Process(current_pid)
    for child in parent.children(recursive=True):
        try:
            child.terminate()
            child.wait(timeout=3)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            pass
    try:
        parent.terminate()
        parent.wait(timeout=3)
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
        pass
    terminate_chrome()

def main():
    while True:
        print("Cronjob Telegram Live...")
        morning_start_time, morning_end_time = get_time_range(morning_start, morning_end)
        afternoon_start_time, afternoon_end_time = get_time_range(afternoon_start, afternoon_end)

        if is_within_timeframe(morning_start_time, morning_end_time) or is_within_timeframe(afternoon_start_time, afternoon_end_time):
            process = subprocess.Popen(["python", "tele_mts.py"])

            while is_within_timeframe(morning_start_time, morning_end_time) or is_within_timeframe(afternoon_start_time, afternoon_end_time):
                time.sleep(60)

            process.terminate()
            print("Terminated Telegram Live.")

            terminate_chrome()
            print("Terminated all Chrome instances.")

        time.sleep(60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        terminate_script()