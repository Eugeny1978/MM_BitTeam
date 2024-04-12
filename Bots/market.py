from time import sleep, time
import pandas as pd
from random import choice, uniform, randint
from DataBase.path_to_base import DATABASE
from Interface.accounts import Accounts
from Connector.bot import get_bot_state
from Connector.logs import jprint, fprint, get_datetime_now, get_time_now

div_line = '-' * 120
pd.options.display.width = None  # Отображение Таблицы на весь Экран
pd.options.display.max_columns = 20  # Макс Кол-во Отображаемых Колонок
pd.options.display.max_rows = 30  # Макс Кол-во Отображаемых Cтрок

DB = DATABASE
SYMBOL = 'DUSD/USDT'
ACCOUNT =  'DUSD_2' # 'DUSD_2' # 'TEST_Korolev'
BOT_NAME = 'Market'
PAUSE = 70 # 100

def get_trade_sides(buys=2, sells=1):
    sides = []  # ('buy', 'buy') # ('buy', 'sell')
    for _ in range(sells):
        sides.append(('sell'))
    for _ in range(buys):
        sides.append(('buy'))
    return tuple(sides)


def main():
    types = ('limit', 'market')  # ('limit', 'limit') # ('limit', 'market')
    sides = get_trade_sides(buys=5, sells=8)

    process = False
    error_message = 'Проверь Подключение к бирже.'

    if get_bot_state(DB, BOT_NAME) == 'Run':
        process = True
        # Инициализация
        accounts = Accounts(DB)
        # Подключение к Аккаунту
        accounts.set_trade_account(ACCOUNT)
        connect = accounts.exchange
        amount_step = connect.markets[SYMBOL]['amountStep']
        price_step = connect.markets[SYMBOL]['priceStep']
        message = f"Бот '{BOT_NAME}' | Режим RUN Запущен | {get_datetime_now()}"
    else:
        message = f"Бот {BOT_NAME} НЕ запущен. Измените Состояние STATE на значение 'Run' | {get_datetime_now()}"
    fprint(message)

    # Основная ПЕТЛЯ
    while get_bot_state(DB, BOT_NAME) == 'Run':

        loop_pause = randint(PAUSE, 2*PAUSE) # варьирую время
        start_time = time()
        try:
            connect.cancel_all_orders(SYMBOL) # удаляю существующие лимитки
        except:
            print(error_message)
        # Задаю Параметры Ордера
        order_amount = round(uniform(10, 50), amount_step) # Интервал Размер Ордера
        order_price = round(uniform(0.987, 1.03), price_step)  # Интервал Цена Ордера
        order_side = choice(sides)
        order_type = choice(types)
        # print(f'Параметры для Ордера: {SYMBOL} | {order_side} | {order_type} | {order_amount = } | {order_price = }')

        # Выставляю Ордер
        if order_type == 'limit': # types[0]: # limit
            try:
                connect.create_order(symbol=SYMBOL, side=order_side, type=order_type, amount=order_amount, price=order_price)
                print(f"Создан Ордер: {SYMBOL} | {order_side} | {order_type} | {order_amount = } | {order_price = }")
            except:
                print(error_message)
        else: # market
            try:
                connect.create_order(symbol=SYMBOL, side=order_side, type=order_type, amount=order_amount)
                print(f"Создан Ордер: {SYMBOL} | {order_side} | {order_type} | {order_amount = }")
            except:
                print(error_message)

        end_time = time()

        print(f"{BOT_NAME} | Процесс Выполнен за {round(end_time - start_time, 3)} сек")
        print(f'Выполняется Пауза {loop_pause} сек. | {get_datetime_now()}')
        sleep(loop_pause)
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
