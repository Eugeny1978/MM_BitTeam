import sqlite3 as sq
import pandas as pd
from Connector.bitteam import BitTeam
from datetime import date, datetime


class BotRemains:
    """
    Бот должен проверять свободные остатки на счету. Исходя из этого ставить/удалять/корректировать дальные ордера
    """

    def __init__(self, database, account_name, symbol, min_remains):
        self.database = database
        self.account_name = account_name
        self.symbol = symbol
        self.min_remains = min_remains
        self.account = self.get_data_account()
        self.connect = self.connect_exchange(self.account)

    def get_data_account(self) -> dict:
        try:
            with sq.connect(self.database) as connect:
                # connect.row_factory = sq.Row
                curs = connect.cursor()
                curs.execute(f"SELECT name, apiKey, secret, mode FROM Accounts WHERE name IS '{self.account_name}'")
                response = curs.fetchone()
                return response # dict(apiKey=acc[1], secret=acc[2], mode=acc[3])
        except Exception as error:
            print('Нет Доступа к базе')
            raise (error)

    def connect_exchange(self):
        pass


if __name__ == '__main__':

    div_line = '-' * 120

    def dprint(*args):
        print(*args, div_line, sep='\n')

    from DataBase.path_to_base import DATABASE

    DB = DATABASE
    ACCOUNT = 'TEST_Luchnik'
    SYMBOL = 'DUSD/USDT'
    MIN_REMAINS = 10_000

    bot = BotRemains(DB, ACCOUNT, SYMBOL, MIN_REMAINS)
    dprint(bot.account)



