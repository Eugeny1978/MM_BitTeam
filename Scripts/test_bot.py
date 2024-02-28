from Connector.old_versions.bitteam import BitTeam
import pandas as pd
import sqlite3 as sq

def is_test_trade_mode(mode: str) -> bool:
    is_test_mode = False
    if mode == 'Test': is_test_mode = True
    return is_test_mode

def format_UPP_symbol(symbol: str):
    """
    Привожу Родной Формат к 'BASECOIN/QUOTECOIN'
    """
    return symbol.upper().replace('_', '/')


class Bot:

    def __init__(self, symbol, volume, zero_price, min_spred, max_spred, num_orders, side_orders, account, database, bot_name):
        self.symbol = symbol
        self.volume = volume
        self.zero_price = zero_price
        self.min_spred = min_spred if side_orders == 'sell' else -min_spred
        self.max_spred = max_spred if side_orders == 'sell' else -max_spred
        self.num_orders = int(num_orders)
        self.side_orders = side_orders
        self.account = account
        self.database = database
        self.apikeys, self.test_mode = self.get_data_from_bd()
        self.exchange, self.steps = self.connect_exchange()
        self.correct_num_orders()
        self.prices = self.get_prices()
        self.amounts = self.get_amounts()
        self.bot_name = bot_name

    def get_data_from_bd(self):
        try:
            with sq.connect(self.database) as connect:
                # connect.row_factory = sq.Row
                curs = connect.cursor()
                curs.execute(f"SELECT apiKey, secret, mode FROM Accounts WHERE name IS '{self.account}'")
                responce = curs.fetchone()
                return dict(apiKey=responce[0], secret=responce[1]), is_test_trade_mode(responce[2])
        except Exception as error:
            print('Нет Доступа к базе | Проверь также имя Аккаунта.')
            raise(error)

    def connect_exchange(self):
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
        if self.side_orders == 'sell': spred = self.min_spred
        if self.side_orders == 'buy': spred = self.max_spred
        price = self.zero_price * (1 + 0.01 * spred) / self.num_orders
        cost_usdt = (self.volume * price)
        if cost_usdt / self.num_orders < self.steps['minAmount']:
            self.num_orders = int(cost_usdt / self.steps['minAmount'])
        return self.num_orders

    def round_price(self, price):
        return round(price, self.steps['priceStep'])

    def round_amount(self, volume):
        return round(volume, self.steps['baseStep'])

    def get_prices(self):
        start_price = self.round_price(self.zero_price * (1 + 0.01 * self.min_spred))
        stop_price = self.round_price(self.zero_price * (1 + 0.01 * self.max_spred))
        delta_price = self.round_price((stop_price - start_price) / self.num_orders)
        # step = float('0.' + '0' * (self.steps['priceStep']-1) + '1')
        # if self.side_orders == 'sell': step = -step
        # prices = [start_price]
        # for price in range(2, self.num_orders):
        #     prices.append(self.round_price(prices[-1] + delta_price))
        # prices.append(stop_price + step)
        prices = [start_price]
        for price in range(1, self.num_orders):
            prices.append(self.round_price(prices[-1] + delta_price))
        return prices

    def get_amounts(self):
        """
        ПОСТОЯННЫЙ Объем
        S = a * n
        """
        return self.round_amount(self.volume / self.num_orders)

    def get_amounts2(self):
        """
        ПОКА В РАЗРАБОТКЕ Также необходимо будет при открытиии ордеров zip(price, volume)
        Линейная Зависимость
        y = a + bx
        S = a*n + 0.5b*n = n(a + 0.5b)
        """
        start = 0.35
        increase = 1
        volume = self.num_orders * (start + 0.5 * increase)



    def create_orders(self):

        actual_prices = self.get_actual_prices()
        orders = pd.DataFrame(columns=('id', 'bot_name', 'symbol', 'side', 'price', 'amount'))
        for price in actual_prices:
            # Здесь возможно необходим будет цикл while для предотвращения сбоев при неработающей бирже
            # Пока все не запишутся успешно дальше продолжать нет смысла!
            try:
                order = self.exchange.create_order(
                    symbol=self.symbol,
                    type='limit',
                    side=self.side_orders,
                    amount=self.amounts,
                    price=price)['result']
                orders.loc[len(orders)] = (order['id'],
                                           self.bot_name,
                                           format_UPP_symbol(order['pair']),
                                           order['side'],
                                           order['price'],
                                           order['quantity'])
            except:
                print(f"Не удалось Создать Ордер: {price = }, {self.amounts = }")
        self.wrire_orders_db(orders)

    def is_other_side_common_orders(self) -> bool:
        """
        Проверить есть ли Органические Ордера с лучшей Ценой в Другую Сторону для sell -> buy и наоборот
        А нужно ли?
        """
        orderbook = self.exchange.fetch_order_book(self.symbol)['result']
        match self.side_orders:
            case 'sell':
                best_price = orderbook['bids'][0][0]
                my_price = max(self.prices)
                return True if best_price > my_price else False
            case 'buy':
                best_price = orderbook['asks'][0][0]
                my_price = min(self.prices)
                return True if best_price < my_price else False

    def get_actual_prices(self):
        actual_prices = self.prices
        orderbook = self.exchange.fetch_order_book(self.symbol)['result']
        match self.side_orders:
            case 'sell':
                bids = orderbook['bids']
                if len(bids):
                    best_price = orderbook['bids'][0][0]
                    actual_prices = [price for price in self.prices if price > best_price]
            case 'buy':
                asks = orderbook['asks']
                if len(asks):
                    best_price = orderbook['asks'][0][0]
                    actual_prices = [price for price in self.prices if price < best_price]
        return actual_prices




    def wrire_orders_db(self, orders: pd.DataFrame):
        try:
            with sq.connect(self.database) as connect:
                # connect.row_factory = sq.Row
                curs = connect.cursor()
                for index, order in orders.iterrows():
                    curs.execute(f""" INSERT INTO Orders VALUES(?, ?, ?, ?, ?, ?)""",
                    (order['id'], order['bot_name'], order['symbol'], order['side'], order['price'], order['amount']))
        except Exception as error:
            print('Нет Доступа к базе')
            raise(error)

    def get_id_orders_db(self):
        try:
            with sq.connect(self.database) as connect:
                # connect.row_factory = sq.Row
                curs = connect.cursor()
                curs.execute(f"SELECT id FROM Orders WHERE bot_name IS '{self.bot_name}'")
                return [order[0] for order in curs]
        except Exception as error:
            print('Нет Доступа к базе')
            raise(error)



if __name__ == '__main__':

    from DataBase.path_to_base import TEST_DB
    import json

    div_line = '-' * 120
    # FORMAT_dt = '%M:%S'
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
    SIDE_ORDERS = 'buy' # 'sell' 'buy'
    ACCOUNT = 'TEST_Luchnik'
    DB = TEST_DB
    BOT_NAME = '1_procent'

    def jprint(data):
        print(json.dumps(data), div_line, sep='\n')


    bot = Bot(SYMBOL, VOLUME, ZERO_PRICE, MIN_SPRED, MAX_SPRED, NUM_ORDERS, SIDE_ORDERS, ACCOUNT, DB, BOT_NAME)
    print(bot.__dict__)
    # ticker = bot.exchange.fetch_ticker("DEL/USDT")
    # jprint(ticker)
    # print(bot.get_prices())
    #
    # bot1 = Bot(SYMBOL, VOLUME, ZERO_PRICE, MIN_SPRED, MAX_SPRED, NUM_ORDERS, 'buy', ACCOUNT, DB)
    # print(bot1.get_prices())
    # bot.exchange.cancel_all_orders()
    #
    # start_time = time()
    # bot.create_orders()
    # stop_time = time()
    # delta_time = stop_time - start_time
    # minutes = int(delta_time / 60)
    # secundes = round((delta_time%60), 3)
    # print('Total sec:', round(delta_time, 3))
    # print(f"{minutes = }, {secundes = }")

    # print(bot.get_id_orders_db())





