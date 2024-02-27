from Connector.bitteam import BitTeam
import sqlite3 as sq


class Trades:

    def __init__(self, account, exchange, database, symbol):
        self.account: str = account
        self.exchange: BitTeam = exchange
        self.database: str = database
        self.symbol = symbol


    def get_trades(self):
        try:
            # Порядок Прямой от Ранних к Поздним сделкам
            trades = self.exchange.fetch_my_trades(symbol=self.symbol, limit=10000, order='ASC')['result']['trades'] #
        except:
            print('Нет соединения с биржей')
            trades = []
        return trades


    def get_last_datetime_db(self):
        try:
            with sq.connect(self.database) as connect:
                # connect.row_factory = sq.Row
                curs = connect.cursor()
                curs.execute(f"SELECT MAX(timestamp) FROM Trades")
                response = curs.fetchall()
                return (response)
        except Exception as error:
            print('Нет Доступа к базе')
            raise (error)




if __name__ == '__main__':
    from Interface.accounts import Accounts
    from DataBase.path_to_base import TEST_DB
    import pandas as pd

    div_line = '-' * 120
    pd.options.display.width = None  # Отображение Таблицы на весь Экран
    pd.options.display.max_columns = 20  # Макс Кол-во Отображаемых Колонок
    pd.options.display.max_rows = 30  # Макс Кол-во Отображаемых Cтрок

    def mprint(*args):
        print(*args, div_line, sep='\n')

    # Инициализация
    accounts = Accounts(TEST_DB)
    # Подключение к Аккаунту
    account = 'Constantin'
    accounts.set_trade_account(account)

    SYMBOL = 'DEL/USDT' # 'DUSD/USDT'

    # account, exchange, database, symbol
    mprint(f"{account = }", f"{accounts.exchange = }", f"{accounts.database}",  f"{SYMBOL}")
    tr = Trades(account, accounts.exchange, accounts.database, SYMBOL)
    mprint(tr.__dict__)

    # balance = accounts.get_balance()
    # mprint(balance)

    exchange_trades = tr.get_trades()
    mprint(exchange_trades)

    last_ts = tr.get_last_datetime_db()
    mprint(last_ts)



