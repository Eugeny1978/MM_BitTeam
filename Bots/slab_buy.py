import pandas as pd
from time import time, sleep
from Connector.bot import Bot, get_bot_state
from Connector.logs import jprint, fprint, get_datetime_now, get_time_now
from DataBase.path_to_base import DATABASE

pd.options.display.width = None  # Отображение Таблицы на весь Экран
pd.options.display.max_columns = 20  # Макс Кол-во Отображаемых Колонок
pd.options.display.max_rows = 30  # Макс Кол-во Отображаемых Cтрок

# PARAMS
SYMBOL = 'DUSD/USDT'
VOLUME = 5_000 # 44571 / (1-0.07) = средневзвешенная цена покупки = 47925.81
ZERO_PRICE = 1
MIN_SPRED = 1.5
MAX_SPRED = 2.49
NUM_ORDERS = 2
SIDE_ORDERS = 'buy' # 'sell' 'buy'
ACCOUNT = 'DUSD_1' # 'DUSD_2' 'TEST_Korolev'
DB = DATABASE
BOT_NAME = 'Slab_Buy'
PAUSE = 60*10 # minutes
SLAB = True

def main():

    process = False
    # 0. Инициализация: Данные Аккаунтов из БД / Соединения с Биржей / Данные по Торгуемым Парам
    if get_bot_state(DB, BOT_NAME) == 'Run':
        process = True
        bot = Bot(SYMBOL, VOLUME, ZERO_PRICE, MIN_SPRED, MAX_SPRED, NUM_ORDERS, SIDE_ORDERS, ACCOUNT, DB, BOT_NAME, SLAB)
        # fprint(*bot.__dict__.items())
        message = f"Бот '{BOT_NAME}' | Режим RUN Запущен | {get_datetime_now()}"
    else:
        message = f"Бот {BOT_NAME} НЕ запущен. Измените Состояние STATE на значение 'Run' | {get_datetime_now()}"
    fprint(message)

    # Основная ПЕТЛЯ
    while get_bot_state(DB, BOT_NAME) == 'Run':

        start_time = time()
        bot.set_orders() # Создаю Ордера
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
            bot.delete_all_orders() # Отменяю Ордера
            fprint(f"Режим STOP. | Ордера ОТМЕНЕНЫ | {get_datetime_now()}")
        case _, True:
            print('Проверь Название Режима в БД')


if __name__ == '__main__':

    main()