from Connector.bitteam import BitTeam   # Конннектор с Биржей
import pandas as pd                     # Работа с Данными в Таблицах (ДатаФреймах)
import sqlite3 as sq                    # Работа с Базой Данных
from random import uniform              # Корректировка Ордеров задействую Случайное отклонение
from typing import Literal              # Создание Классов Перечислений

SideType = Literal['buy', 'sell']
# DBType = Literal['TEST_DB', 'DATABASE']

def get_bot_state(database, bot_name):
    """
    Получение Значения Режима Работы Бота
    """
    with sq.connect(database) as connect:
        curs = connect.cursor()
        curs.execute(f"SELECT state FROM Bots WHERE name IS '{bot_name}'")
        return curs.fetchone()[0]

class Bot:

    def __init__(self, symbol, volume, zero_price, min_spred, max_spred, num_orders, side_orders, account, database, bot_name):
        """
        symbol: "baseCOIN/quoteCOIN" Торгуемая Пара
        volume: Общий объем Средств (в базовой Валюте ?)
        zero_price: Начальная Цена от которой отсчитываются Уровни Диапазона
        min_spred: Мин. Спред Между Начальной Ценой и Ордерами
        max_spred: Макс. Спред между Начальной Ценой и Ордерами. Последний Ордер выставляется на цене -1 межордерный Интервал
        num_orders: Полное Кол-во Ордеров на Интервале. Если в стакане есть Цены лучше, то часть Ордеров не выставляется
        side_orders: Сторона Ордеров (sell, buy)
        account: Имя Аккаунта в Базе Данных
        database: Путь к Базе Данных
        apikeys: API Ключи Аккаунта
        test_mode: Флаг Тестового Режима Торговли (на тестовом Сервере)
        exchange: Авторизированное Соединение с Биржей
        steps: Шаги Цены, Объема, Минимиальный Объем Ордера
        prices: Полный Список Цен по всему диапазону
        amounts: Номинальный Размер Каждого Ордера. Перед выставлением корректируется в случ некотором интервале
        bot_name: Имя Бота в Базе Данных
        """
        self.symbol: str = symbol
        self.volume: float = volume
        self.zero_price: float = zero_price
        self.min_spred: float = min_spred if side_orders == 'sell' else -min_spred
        self.max_spred: float = max_spred if side_orders == 'sell' else -max_spred
        self.num_orders: int = int(num_orders)
        self.side_orders: SideType = side_orders
        self.account: str = account
        self.database: str = database
        self.apikeys, self.test_mode = self.get_data_from_db() # dict, bool
        self.exchange: BitTeam = self.connect_exchange() # dict , self.steps
        self.steps: dict = self.get_steps()
        self.correct_num_orders()
        self.prices: list = self.get_prices()
        self.amounts: float = self.get_amounts()
        self.bot_name: str = bot_name

    @staticmethod
    def is_test_trade_mode(mode: str) -> bool:
        return True if mode == 'Test' else False

    def round_price(self, price):
        return round(price, self.steps['priceStep'])

    def round_amount(self, volume):
        return round(volume, self.steps['baseStep'])

    def get_random_amount(self):
        return self.round_amount(uniform(0.8, 1.2) * self.amounts)

    def get_data_from_db(self):
        """
        Данные по Аккаунту из Базы Данных
        """
        try:
            with sq.connect(self.database) as connect:
                # connect.row_factory = sq.Row
                curs = connect.cursor()
                curs.execute(f"SELECT apiKey, secret, mode FROM Accounts WHERE name IS '{self.account}'")
                responce = curs.fetchone()
                return dict(apiKey=responce[0], secret=responce[1]), self.is_test_trade_mode(responce[2])
        except Exception as error:
            print('Нет Доступа к базе | Проверь также имя Аккаунта.')
            raise (error)

    def connect_exchange(self):
        """
        Соединение с Биржей. Учитывается режим торговли Реальный или Тестовый
        """
        try:
            exchange = BitTeam()
            if self.test_mode:
                exchange.set_test_mode(self.test_mode)  # перейти в режим тестовой торговли
                exchange.load_markets()                 # обновить инфо по тикерам
        except Exception as error:
            print('Биржа НЕдоступна')
            raise (error)
        try:
            exchange.account = self.apikeys             # авторизация
            # для проверки ключей, возможно, нужен любой запрос
        except Exception as error:
            print('API Ключи НЕдействительны')
            raise (error)
        return exchange

    def get_steps(self):
        self.steps = self.exchange.markets[self.symbol]
        return self.steps

    def correct_num_orders(self):
        """
        РАЗОБРАТЬСЯ ИСПРАВИТЬ ОКРУГЛЕНИЕ и тд коррректность!!!
        Корректирую Число Ордеров,
        тк возможны случаи когда можно попытаться мылым объемом зайти на больш количество Ордеров
        """
        if self.side_orders == 'sell':
            spred = self.min_spred
        else: # 'buy'
            spred = self.max_spred
        price = self.zero_price * (1 + 0.01 * spred) # / self.num_orders
        cost_usdt = (self.volume * price)
        if cost_usdt / self.num_orders < self.steps['limit_usd']:
            self.num_orders = int(cost_usdt / self.steps['limit_usd'])
            print(f"Кол-во Ордеров измененено на {self.num_orders}")
        return self.num_orders

    def get_prices(self):
        """
        Получение Массива цен по Всему Диапазону
        В зависимости от ситуации в стакана часть цен может отсекаться
        Все что хуже лучших цен на рынке
        """
        start_price = self.round_price(self.zero_price * (1 + 0.01 * self.min_spred))
        stop_price = self.round_price(self.zero_price * (1 + 0.01 * self.max_spred))
        delta_price = self.round_price((stop_price - start_price) / self.num_orders)
        prices = [start_price]
        for price in range(1, self.num_orders):
            prices.append(self.round_price(prices[-1] + delta_price))
        return prices

    def get_amounts(self):
        """
        ПОСТОЯННЫЙ Объем
        S = a * n
        Номинальный Объем. При Создании Ордеров можно дополнительно варьировать в заданном интервале изменений
        """
        return self.round_amount(self.volume / self.num_orders)

    def get_actual_orderbook_prices(self):
        """
        Получение Актуальных Цен исходя из ситуации в стакане
        """
        actual_prices = self.prices
        orderbook = self.exchange.fetch_order_book(self.symbol)['result']
        match self.side_orders:
            case 'sell':
                bids = orderbook['bids']
                if len(bids):
                    best_price = float(bids[0][0])
                    actual_prices = [price for price in self.prices if price > best_price]
            case 'buy':
                asks = orderbook['asks']
                if len(asks):
                    best_price = float(asks[0][0])
                    actual_prices = [price for price in self.prices if price < best_price]
        return actual_prices

    def get_actual_prices(self):
        """
        Определение Цен по которым нет моих Ордеров. Контролирую исполнение своих ордеров
        """
        check_prices = self.get_actual_orderbook_prices()
        my_orders = self.get_my_orders() # сделать получение только ордеров на интервале
        if not len(my_orders):
            return check_prices
        return [price for price in check_prices if price not in my_orders['price'].values]

    def get_orders(self) -> dict:
        try:
            my_orders: dict = self.exchange.fetch_orders(self.symbol, limit=10000)['result']
        except:
            my_orders = dict(count=0)
            print('Нет Подключения к базе')
        return my_orders

    def orders_to_dataframe(self, orders: dict) -> pd.DataFrame:
        df = pd.DataFrame(columns=('id', 'symbol', 'side', 'price', 'amount'))
        for order in orders['orders']:
            df.loc[len(df)] = (order['id'],
                               self.exchange.format_pair(order['pair']),
                               order['side'],
                               float(order['price']),
                               float(order['quantity'])
                               )
        return df

    def get_my_orders(self) -> pd.DataFrame:
        """
        Из всех Ордеров Аккаунта выбираю ордера на Моем Интервале и Направлении
        Интервал реализован как   min_price <= price >= max_price
        Можно реализовать по конкретным ценам на интервале используя self.prices - но думаю работать будет медленее
        """
        orders = self.orders_to_dataframe(self.get_orders())
        filter = f"(side == '{self.side_orders}') and (price >= {min(self.prices)}) and (price <= {max(self.prices)})"
        my_orders = orders.query(filter).reset_index(drop=True)
        return my_orders

    def set_orders(self):
        """
        Создаю Ордера на уровнях Актуальных Цен
        """
        try:
            actual_prices = self.get_actual_prices()
            print(f"Кол-во Актуальных (свободных) Цен: {len(actual_prices)}")
            print(f"{actual_prices = }")
        except Exception as error:
            print(error)
            print(f'Не удалось получить Актуальные Цены. Нет соединения с Биржей!')
            actual_prices = []
        for price in actual_prices:
            # При неработающей бирже он пропустит эти Действия НЕ вывалится с ошибкой
            # В след Цикле он должен выявить что по этим ценам не стоит ордеров и снова попытаться выставить ордера.
            rand_amount = self.get_random_amount()
            order_info = f"{self.symbol} | {self.side_orders.upper()} | Amount: {rand_amount} | Price: {price}"
            try:
                self.exchange.create_order(
                    symbol=self.symbol,
                    type='limit',
                    side=self.side_orders,
                    amount= rand_amount,
                    price=price)['result']
                print(f'Создан Ордер | {order_info}')
            except:
                print(f"НЕ Удалось Создать Ордер | {order_info}")

    def delete_all_orders(self):
        """
        Функция для отмены ВСЕХ ордеров на своем Интервале.
        """
        # my_orders = self.get_my_orders() ###
        # for order_id in my_orders['id'].values:
        #     try:
        #         self.exchange.cancel_order(id=order_id)
        #         print(f"Удален Ордер {order_id = }")
        #     except:
        #         print(f"Не получилось удалить Ордер {order_id = }")
        my_orders = self.get_my_orders() ###
        for index, order in my_orders.iterrows():
            odrer_info = f"ID: {order['id']} | Price: {order['price']}"
            try:
                self.exchange.cancel_order(id=order['id'])
                print("Удален Ордер", odrer_info)
            except:
                print("НЕ получилось удалить Ордер", odrer_info)


if __name__ == '__main__':

    from DataBase.path_to_base import TEST_DB
    import json
    # from time import time

    div_line = '-' * 120
    pd.options.display.width = None  # Отображение Таблицы на весь Экран
    pd.options.display.max_columns = 20  # Макс Кол-во Отображаемых Колонок
    pd.options.display.max_rows = 30  # Макс Кол-во Отображаемых Cтрок

    # PARAMS
    SYMBOL = 'DUSD/USDT'
    VOLUME = 1000
    ZERO_PRICE = 1
    MIN_SPRED = 1
    MAX_SPRED = 2
    NUM_ORDERS = 10
    SIDE_ORDERS = 'sell' # 'sell' 'buy'
    ACCOUNT = 'TEST_Luchnik'
    DB = TEST_DB
    BOT_NAME = '1_procent'

    def jprint(data):
        print(json.dumps(data), div_line, sep='\n')

    def mprint(*args):
        print(*args, div_line, sep='\n')


    bot = Bot(SYMBOL, VOLUME, ZERO_PRICE, MIN_SPRED, MAX_SPRED, NUM_ORDERS, SIDE_ORDERS, ACCOUNT, DB, BOT_NAME)
    # print(bot.__dict__)
    # bot.exchange.cancel_all_orders()

    check_prices = bot.get_actual_orderbook_prices()
    actual_prices = bot.get_actual_prices()
    mprint()
    mprint(bot.prices)
    mprint(check_prices)
    mprint(actual_prices)
    # mprint(bot.exchange.markets)
    # mprint(bot.steps)

    # bot.set_orders()
    #
    my_orders = bot.get_my_orders()
    mprint(my_orders)
    bot.delete_all_orders()

