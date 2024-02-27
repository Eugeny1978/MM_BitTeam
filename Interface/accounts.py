import sqlite3 as sq
from datetime import datetime
import pandas as pd
from Connector.bitteam import BitTeam
from DataBase.path_to_base import TEST_DB, DATABASE

FORMAT_dt = '%Y-%m-%d %H:%M:%S'
ORDER_COLUMNS = ('id', 'symbol', 'type', 'side', 'price', 'amount', 'cost', 'ramaining', 'datetime')
TRADES_COLUMNS  = ('id', 'symbol', 'side', 'price', 'amount', 'cost', 'makerUserId', 'takerUserId', 'datetime')


def make_style_df(styler):
    # styler.set_caption("Open ORDERS")
    styler.format(precision=6, thousands=" ", decimal=".")
    styler.format_index(str.upper, axis=1)
    return styler

def format_pair_symbol(pair: str) -> str:
    return pair.replace('_', '/').upper()

def format_coin_symbol(coin: str) -> str:
    return coin + '/USDT'.upper()


def format_datetime(datetime: str) -> str:
    """'2023-11-10T15:33:01.842Z' -> '2023-11-10 15:33:01'"""
    return datetime[:-5].replace('T', ' ')

def calc_cost(price: float, amount: float) -> float:
    return round(price * amount, 2)

def calc_remaining(executed: float, amount: float) -> float:
    return amount - executed

def is_test_trade_mode(mode: str) -> bool:
    return True if mode == 'Test' else False


class Accounts:

    def __init__(self, database):
        self.database = database
        self.data = self.get_accounts()
        self.acc_names = self.data.keys()
        self.trade_account = ''
        self.trade_keys = ''
        self.exchange = self.connect_exchange()
        self.balance = pd.DataFrame()
        self.cost_balance = pd.DataFrame()
        self.orders = pd.DataFrame(columns=ORDER_COLUMNS)
        self.trades = pd.DataFrame(columns=TRADES_COLUMNS)

    def get_accounts(self) -> dict:
        try:
            with sq.connect(self.database) as connect:
                # connect.row_factory = sq.Row
                curs = connect.cursor()
                curs.execute(f"SELECT name, apiKey, secret, mode FROM Accounts")
                accounts = dict()
                for acc in curs:
                    accounts[acc[0]] = dict(apiKey=acc[1], secret=acc[2], mode=acc[3])
                return accounts
        except Exception as error:
            print('Нет Доступа к базе')
            raise(error)

    def set_trade_account(self, account):
        if account:
            self.trade_account = account
            self.trade_keys = self.data[account]
            self.test_mode = is_test_trade_mode(self.data[account]['mode'])
            self.connect_exchange()

    def connect_exchange(self):
        # try:
        #     self.exchange = BitTeam()
        #
        # except Exception as error:
        #     print('Биржа НЕдоступна')
        #     raise(error)
        # if self.trade_account:
        #     try:
        #         self.exchange = BitTeam(self.trade_keys)
        #     except Exception as error:
        #         print('Биржа НЕдоступна')
        #         raise (error)
        # return self.exchange

        self.exchange = BitTeam()
        if self.trade_account:
            try:
                self.exchange = BitTeam(self.trade_keys)
                self.exchange.set_test_mode(self.test_mode)
                self.exchange.info_tickers()
            except Exception as error:
                print('Биржа НЕдоступна')
                raise (error)
        return self.exchange


        # try:
        #     exchange = BitTeam()
        #     exchange.set_test_mode(self.test_mode)
        #     exchange.info_tickers() # обязательно освежить инфу по тикерам
        # except Exception as error:
        #     print('Биржа НЕдоступна')
        #     raise(error)
        # try:
        #     exchange = BitTeam(self.apikeys)
        #     exchange.set_test_mode(self.test_mode)
        #     steps = self.get_steps(exchange.fetch_ticker(self.symbol))
        # except Exception as error:
        #     print('API Ключи НЕдействительны')
        #     raise (error)
        # return exchange, steps

    def get_balance(self):
        try:
            balance = self.exchange.fetch_balance()
            indexes = ['free', 'used', 'total']
            columns = [balance['free'], balance['used'], balance['total']]
            df = pd.DataFrame(columns, index=indexes)
            df = df.astype(float)
            df_compact = df.loc[:, (df != 0).any(axis=0)]  # убирает Столбцы с 0 значениями
            # df_compact = df_0.loc[:, (df_0 != '0').any(axis=0)]  # если числа в виде строк
        except Exception as error:
            df_compact = None
            print(error)
        self.balance = df_compact
        return self.balance

    def get_cost_balanse(self):
        if not self.trade_account:
            self.cost_balance = pd.DataFrame()
            return self.cost_balance

        df = self.balance.copy()
        for column in df.columns:
            if column == 'USDT':
                df[column] = round(df[column], 2)
                continue
            symbol = format_coin_symbol(column)
            try:
                price = float(self.exchange.fetch_ticker(symbol)['result']['pair']['lastSell'])
                df[column] = round(df[column] * price, 2)
            except:
                print(f"{symbol} | Не удалось получить Последнюю Цену Продажи")
        self.cost_balance = df
        return self.cost_balance

    def get_open_orders(self):
        df = pd.DataFrame(columns=ORDER_COLUMNS)
        if not self.trade_account:
            self.orders = df
            return self.orders
        response = self.exchange.fetch_orders()
        if not response['result']['count']:
            self.orders = df
            return self.orders
        orders = response['result']['orders']
        # ('id', 'symbol', 'type', 'side', 'price', 'amount', 'cost', 'ramaining', 'datetime')
        for order in orders:
            price, amount = float(order['price']), float(order['quantity'])
            df.loc[len(df)] = (
                str(order['id']),
                format_pair_symbol(order['pair']),
                order['type'],
                order['side'],
                price,
                amount,
                calc_cost(price, amount),
                calc_remaining(float(order['executed']), amount),
                format_datetime(order['updatedAt'])
            )
        self.orders = df
        return self.orders

    def get_trades(self):
        df = pd.DataFrame(columns=TRADES_COLUMNS)
        if not self.trade_account:
            self.trades = df
            return self.trades
        response = self.exchange.fetch_my_trades(limit=1000)
        if not response['result']['count']:
            self.orders = df
            return self.orders
        trades = response['result']['trades']
        # ('id', 'symbol', 'side', 'price', 'amount', 'cost', 'makerUserId', 'takerUserId', 'datetime')
        for trade in trades:
            price, amount = float(trade['price']), float(trade['quantity'])
            df.loc[len(df)] = (
                str(trade['id']),
                format_pair_symbol(trade['pair']),
                trade['side'],
                price,
                amount,
                calc_cost(price, amount),
                trade['makerUserId'],
                trade['takerUserId'],
                format_datetime(trade['updatedAt'])
            )
        self.orders = df
        return self.orders



if __name__ == '__main__':

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
    # accounts.exchange.set_test_mode(True) # Тестовый режим
    mprint('Account:',account, accounts.exchange)

    # Таблица Баланса
    balance = accounts.get_balance()
    mprint('Balance:', balance)

    # Таблица Стоимости в USDT Баланса
    cost_balance = accounts.get_cost_balanse()
    mprint('Cost Balance:', cost_balance)

    # Таблица Ордеров. Отдельно SELL отдельно BUY
    orders = accounts.get_open_orders()
    mprint('SELL Orders', orders.query("side == 'sell'"))
    mprint('BUY Orders', orders.query("side == 'buy'"))

    # Таблица Сделок
    trades = accounts.get_trades()
    mprint('TRADES:', trades)




