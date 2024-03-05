from Interface.accounts import Accounts, make_style_df
from datetime import date, timedelta, time, datetime


if __name__ == '__main__':

    from Connector.logs import fprint
    from DataBase.path_to_base import TEST_DB, DATABASE
    import pandas as pd

    div_line = '-' * 120
    pd.options.display.width = None  # Отображение Таблицы на весь Экран
    pd.options.display.max_columns = 20  # Макс Кол-во Отображаемых Колонок
    pd.options.display.max_rows = 30  # Макс Кол-во Отображаемых Cтрок

    DB = TEST_DB
    SYMBOL = 'DUSD/USDT'
    ACCOUNT = 'TEST_Korolev'
    BOT_NAME = 'Market'
    PAUSE = 60

    # Инициализация
    accounts = Accounts(DB)
    # Подключение к Аккаунту
    accounts.set_trade_account(ACCOUNT)



