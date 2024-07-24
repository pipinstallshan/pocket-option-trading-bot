from datetime import datetime, timedelta

utc_now = datetime.utcnow()
utc_minus_3 = utc_now - timedelta(hours=3)
current_time = utc_minus_3.strftime('%H:%M')
one_minute_before_trade_time = (current_time.split(":")[0] + ":") + (("0" + str((int(current_time.split(":")[1])+1))) if len(str((int(current_time.split(":")[1])+1))) == 1 else str((int(current_time.split(":")[1])+1)))
print(current_time)
print(one_minute_before_trade_time)