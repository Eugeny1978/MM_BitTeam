from datetime import date, timedelta, time, datetime
from time import sleep
import pandas as pd
from random import choice, uniform
from DataBase.path_to_base import TEST_DB, DATABASE
from Interface.accounts import Accounts
from Connector.bot import get_bot_state
from Connector.logs import jprint, fprint, get_datetime_now, get_time_now

div_line = '-' * 120
pd.options.display.width = None  # Отображение Таблицы на весь Экран
pd.options.display.max_columns = 20  # Макс Кол-во Отображаемых Колонок
pd.options.display.max_rows = 30  # Макс Кол-во Отображаемых Cтрок

DB = TEST_DB
SYMBOL = 'DUSD/USDT'
ACCOUNT = 'TEST_Korolev'
BOT_NAME = 'Market'
PAUSE = 100

sides = ('buy', 'sell')
types = ('limit', 'market')

def main():


    # Инициализация
    accounts = Accounts(DB)
    # Подключение к Аккаунту
    accounts.set_trade_account(ACCOUNT)
    connect = accounts.exchange

    process = False
    # Основная ПЕТЛЯ
    while get_bot_state(DB, BOT_NAME):
        process = True
        start_time = time()

        connect.cancel_all_orders() # удаляю существующие лимитки
        # Задаю Параметры Ордера
        order_price = round(uniform(0.95, 1.05), 6)
        order_amount = round(uniform(5, 200), 6)
        order_side = choice(sides)
        order_type = choice(types)
        # Выставляю Ордер
        if order_type == types[0]: # limit
            connect.create_order(symbol=SYMBOL, side=order_side, type=order_type, amount=order_amount, price=order_price)
        else: # market
            connect.create_order(symbol=SYMBOL, side=order_side, type=order_type, amount=order_amount)

        end_time = time()

        print(f"{BOT_NAME} | Процесс Выполнен за {round(end_time - start_time, 3)} сек")
        print(f'Выполняется Пауза {PAUSE} сек. | {get_datetime_now()}')
        sleep(PAUSE)
        fprint(f'Пауза Завершена. | {get_datetime_now()}')

        match get_bot_state(DB, BOT_NAME), process:
            case 'Run', True:
                print('Что-то не так | RUN')
            case 'Pause', True:
                fprint(f"Режим PAUSE. | Ордера остались на Бирже. | {get_datetime_now()}")
            case 'Stop', True:
                connect.cancel_all_orders()  # Отменяю Ордера
                fprint(f"Режим STOP. | Ордера ОТМЕНЕНЫ | {get_datetime_now()}")
            case _, True:
                print('Проверь Название Режима в БД')


if __name__ == '__main__':
    main()
