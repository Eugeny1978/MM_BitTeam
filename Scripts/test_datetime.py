import datetime
import pytz

stamp = 1700816015

date = datetime.datetime.timestamp(datetime.datetime.now())
print(date)

date1 = datetime.datetime.fromtimestamp(stamp)
print(date1)

date2 = datetime.datetime.fromtimestamp(stamp, tz=pytz.utc)
print(date2)