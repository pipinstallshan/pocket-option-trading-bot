import os
import time
import pytz
import psutil
import subprocess
from datetime import datetime, timedelta

morning_start = "08:00"
morning_end = "12:00"
afternoon_start = "14:00"
afternoon_end = "18:00"
evening_start = "20:00"
evening_end = "00:00"

london_tz = pytz.timezone('Europe/London')

def get_time_range(start, end):
    today = datetime.now(london_tz).date()
    start_time = london_tz.localize(datetime.strptime(f"{today} {start}", "%Y-%m-%d %H:%M"))
    if end == "00:00":
        tomorrow = today + timedelta(days=1)
        end_time = london_tz.localize(datetime.strptime(f"{tomorrow} 00:00", "%Y-%m-%d %H:%M"))
    else:
        end_time = london_tz.localize(datetime.strptime(f"{today} {end}", "%Y-%m-%d %H:%M"))
    return start_time, end_time

def is_within_timeframe(start, end):
    now = datetime.now(london_tz)
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
        print("Cronjob Pocket Live...")
        morning_start_time, morning_end_time = get_time_range(morning_start, morning_end)
        afternoon_start_time, afternoon_end_time = get_time_range(afternoon_start, afternoon_end)
        evening_start_time, evening_end_time = get_time_range(evening_start, evening_end)

        if (is_within_timeframe(morning_start_time, morning_end_time) or
            is_within_timeframe(afternoon_start_time, afternoon_end_time) or
            is_within_timeframe(evening_start_time, evening_end_time)):
            
            process = subprocess.Popen(["python", "pocket_mts.py"])

            while (is_within_timeframe(morning_start_time, morning_end_time) or
                   is_within_timeframe(afternoon_start_time, afternoon_end_time) or
                   is_within_timeframe(evening_start_time, evening_end_time)):
                time.sleep(60)

            process.terminate()
            print("Terminated Pocket Live.")

            terminate_chrome()
            print("Terminated all Chrome instances.")

        time.sleep(60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        terminate_script()
