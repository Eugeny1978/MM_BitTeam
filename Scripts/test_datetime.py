import datetime
import pytz

# timestampz

stamp = 1700816015

date = datetime.datetime.timestamp(datetime.datetime.now())
print(date)

date1 = datetime.datetime.fromtimestamp(stamp)
print(date1)

date2 = datetime.datetime.fromtimestamp(stamp, tz=pytz.utc)
print(date2)

date4 = "2024-02-28T10:39:11.133Z"
d5 = datetime.datetime.fromisoformat(date4)
print(d5)
form = ("%Y-%m-%dT%H:%M:%S.%fZ") # "%Y-%m-%dT%H:%M:%S.%fZ" '%Y-%m-%dT%H:%M:%S.'
d7 = d5.strftime(form)
d8 = d7[:-4] + "Z"
d9 = d7[slice(0,-4)] + 'Z' # d7[slice(0,-4, 1)] + 'Z'
print(d7)
print(d8)
print(d9)

d10 = datetime.datetime.timestamp(datetime.datetime.now())
print(d10)
d11 = datetime.datetime.fromtimestamp(d10, tz=pytz.utc)
print(d11)
d12 = d11.strftime(form)[:-4]+'Z' # Можно попробовать закидывать без среза строку
print(d12)





