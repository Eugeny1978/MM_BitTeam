from Connector.bitteam import BitTeam
import pandas as pd
import sqlite3 as sq

def is_test_trade_mode(mode: str) -> bool:
    return True if mode == 'Test' else False

class Contragent:

    def __init__(self, symbol, account, database):
        self.symbol = symbol
        self.account = account
        self.database = database
        self.apikeys, self.test_mode = self.get_data_from_db()
        self.exchange, self.steps = self.connect_exchange()

    def round_price(self, price):
        return round(price, self.steps['priceStep'])

    def round_amount(self, volume):
        return round(volume, self.steps['baseStep'])

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
            exchange.info_tickers()  # обязательно освежить инфу по тикерам
        except Exception as error:
            print('Биржа НЕдоступна')
            raise (error)
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
        return dict(priceStep=data['settings']['price_view_min'],
                    baseStep=data['baseStep'],
                    quoteStep=data['quoteStep'],
                    minAmount=float(data['settings']['limit_usd']))



if __name__ == '__main__':
    from DataBase.path_to_base import TEST_DB
    import json
    from time import time

    div_line = '-' * 120
    pd.options.display.width = None  # Отображение Таблицы на весь Экран
    pd.options.display.max_columns = 20  # Макс Кол-во Отображаемых Колонок
    pd.options.display.max_rows = 30  # Макс Кол-во Отображаемых Cтрок

    # PARAMS
    SYMBOL = 'DUSD/USDT'
    ACCOUNT =  'TEST_Luchnik' # 'TEST_Korolev'
    DB = TEST_DB

    agent = Contragent(SYMBOL, ACCOUNT, DB)
    agent.exchange.cancel_all_orders()
    # agent.exchange.create_order(SYMBOL, 'limit', 'buy', 50, 1.0143)
    # agent.exchange.create_order(SYMBOL, 'limit', 'sell', 50, 0.9864)

    # agent.exchange.create_order(SYMBOL, 'limit', 'buy', 50, 0.982)
    # agent.exchange.create_order(SYMBOL, 'limit', 'buy', 50, 0.981)
