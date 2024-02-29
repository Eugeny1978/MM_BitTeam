import json
from datetime import datetime, timedelta, time, date

div_line = '-' * 120

def jprint(data):
    print(json.dumps(data), div_line, sep='\n')

def fprint(*args):
    print(*args, div_line, sep='\n')

def get_time_now() -> str:
    return datetime.now().strftime('%H:%M:%S')

def get_datetime_now() -> str:
    return datetime.now().strftime('%Y-%m-%d | %H:%M:%S')

if __name__ == '__main__':
    fprint(get_datetime_now())
    fprint(get_time_now())