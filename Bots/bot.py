from Connector.bitteam import BitTeam
import pandas as pd
import sqlite3 as sq
from random import uniform
from typing import Literal      # Создание Классов Перечислений

SideType = Literal['buy', 'sell']
# DBType = Literal['TEST_DB', 'DATABASE']

def is_test_trade_mode(mode: str) -> bool:
    return True if mode == 'Test' else False

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
        self.exchange, self.steps = self.connect_exchange() # BitTeam, dict
        self.correct_num_orders()
        self.prices: list = self.get_prices()
        self.amounts: float = self.get_amounts()
        self.bot_name: str = bot_name


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
                return dict(apiKey=responce[0], secret=responce[1]), is_test_trade_mode(responce[2])
        except Exception as error:
            print('Нет Доступа к базе | Проверь также имя Аккаунта.')
            raise (error)

    def connect_exchange(self):
        """
        Соединение с Биржей. Учитывается режи м торговли Реальный или Тестовый
        """
        try:
            exchange = BitTeam()
            exchange.set_test_mode(self.test_mode)
            exchange.info_tickers() # обязательно освежить инфу по тикерам
        except Exception as error:
            print('Биржа НЕдоступна')
            raise(error)
        try:
            exchange = BitTeam(self.apikeys)
            exchange.set_test_mode(self.test_mode)
            steps = self.get_steps(exchange.fetch_ticker(self.symbol))
        except Exception as error:
            print('API Ключи НЕдействительны')
            raise (error)
        return exchange, steps

    def get_steps(self, tiker: dict):
        data = tiker['result']['pair']
        return dict(priceStep = data['settings']['price_view_min'],
                    baseStep = data['baseStep'],
                    quoteStep = data['quoteStep'],
                    minAmount = float(data['settings']['limit_usd']) )

    def correct_num_orders(self):
        """
        Корректирую Число Ордеров,
        тк возможны случаи когда можно попытаться мылым объемом зайти на больш количество Ордеров
        """
        if self.side_orders == 'sell':
            spred = self.min_spred
        else: # 'buy'
            spred = self.max_spred
        price = self.zero_price * (1 + 0.01 * spred) / self.num_orders
        cost_usdt = (self.volume * price)
        if cost_usdt / self.num_orders < self.steps['minAmount']:
            self.num_orders = int(cost_usdt / self.steps['minAmount'])
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

    def get_my_orders(self) -> dict:
        try:
            my_orders: dict = self.exchange.fetch_orders(self.symbol, limit=10000)['result']
        except:
            my_orders = dict(count=0)
            print('Нет Подключения к базе')
        return my_orders

    def get_actual_prices(self):
        """
        Определение Цен по которым нет моих Ордеров. Контролирую исполнение своих ордеров
        """
        check_prices = self.get_actual_orderbook_prices()
        my_orders = self.get_my_orders()
        if not my_orders['count']:
            return check_prices
        order_prices = [float(order['price']) for order in my_orders['orders']]
        return [price for price in check_prices if price not in order_prices]

    def set_orders(self):
        """
        Создаю Ордера на уровнях Актуальных Цен
        """
        actual_prices = self.get_actual_prices()
        for price in actual_prices:
            # При неработающей бирже он пропустит эти Действия НЕ вывалится с ошибкой
            # В след Цикле он должен выявить что по этим ценам не стоит ордеров и снова попытаться выставить ордера.
            try:
                self.exchange.create_order(
                    symbol=self.symbol,
                    type='limit',
                    side=self.side_orders,
                    amount=self.get_random_amount(),
                    price=price)['result']
                # print(f'Создан Ордер {price = }')
            except:
                print(f"Не удалось Создать Ордер: {price = }, {self.amounts = }")

    def delete_all_orders(self):
        """
        Функция для отмены ВСЕХ ордеров на своем Интервале.
        """

        orders = self.get_my_orders()
        # Фильтрую
        # {key: val for key, val in d.items() if key in ('a', 'c', 'e')}
        # {key: val for key, val in d.items() if val > 3}
        # {key: val for key, val in d.items() if key in ('a', 'c', 'e') and val > 1}
        sells = {key: value for key, value in orders.items() if key == 'side' and value == 'sell'}
        buys = {key: value for key, value in orders.items() if key == 'side' and value == 'buy'}
        match self.side_orders:
            case 'sell':
                pass
            case 'buy':
                pass
        return sells, buys



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
    NUM_ORDERS = 5
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

    bot.set_orders()

    sells, buys = bot.delete_all_orders()
    mprint(sells, buys)
