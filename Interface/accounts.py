import sqlite3 as sq
import pandas as pd
from Connector.bitteam import BitTeam
from datetime import date, datetime

FORMAT_dt = '%Y-%m-%d %H:%M:%S'
ORDER_COLUMNS = ('id', 'symbol', 'type', 'side', 'price', 'amount', 'cost', 'ramaining', 'datetime')
TRADES_COLUMNS  = ('id', 'symbol', 'side', 'price', 'amount', 'cost', 'makerId', 'takerId', 'fee', 'datetime')
RESULTS_COLUMNS = ('side', 'amount', 'cost', 'fee', 'price')


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
    return round(price * amount, 6)

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
        self.test_mode = False
        self.exchange = self.connect_exchange()
        self.balance = pd.DataFrame()
        self.cost_balance = pd.DataFrame()
        self.orders = pd.DataFrame(columns=ORDER_COLUMNS)
        self.trades = pd.DataFrame(columns=TRADES_COLUMNS)
        self.results = ('', ) #pd.DataFrame(columns=RESULTS_COLUMNS)
        self.symbol = ''

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
            self.exchange = self.connect_exchange()

    def connect_exchange(self):
        try:
            exchange = BitTeam()
        except Exception as error:
            print('Биржа НЕдоступна')
            raise (error)
        if self.trade_account:
            try:
                if self.test_mode:
                    exchange.set_test_mode(self.test_mode)
                    exchange.load_markets()
                exchange.account = self.trade_keys
                # для проверки ключей, возможно, нужен любой запрос
            except Exception as error:
                print('API Ключи НЕдействительны')
                raise (error)
        return exchange

    def get_balance(self):
        try:
            balance = self.exchange.fetch_balance()['result']
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

    def get_trades(self, symbol='', startTime=0, endTime=0):
        df = pd.DataFrame(columns=TRADES_COLUMNS)
        self.symbol = symbol
        if not self.trade_account:
            self.trades = df
            return self.trades
        response = self.exchange.fetch_my_trades_test(symbol=symbol, startTime=startTime, endTime=endTime) #####
        if not response['result']['count']:
            self.trades = df
            return self.trades
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
                self.get_fee(trade),
                format_datetime(trade['updatedAt']) # поменять на преобразованное значение поля 'timestamp'
            )
        # self.symbol = symbol
        self.trades = df
        return self.trades

    def get_fee(self, trade: dict) -> float:
        match trade['isCurrentSide']:
            case 'maker':
                type_fee = trade['feeMaker']
            case 'taker':
                type_fee = trade['feeTaker']
        fee = float(type_fee['amount'])
        # if trade['side'] == 'sell':
        #     fee = fee  * round(float(trade['price']), 6)
        return fee # уточнить в какой валюте

    @staticmethod
    def round_2(number):
        return round(number, 4)

    def get_trade_results(self) -> dict:
        """
        Возвращает Словарь внутри 2 датафрейма с результатами. Без Учета Коммисий и с учетом
        """
        deals = pd.DataFrame(columns=RESULTS_COLUMNS)
        for side in ('buy', 'sell'):
            data = self.trades.query(f"side == '{side}'").copy().reset_index(drop=True)[list(RESULTS_COLUMNS)]
            sum_amount = self.round_2(data['amount'].sum())
            sum_cost = self.round_2(data['cost'].sum())
            sum_fee = self.round_2(data['fee'].sum())
            aw_price = self.__calc_aw_price(sum_cost, sum_amount) # round((sum_cost / sum_amount), 6)
            deals.loc[len(deals)] = (side.upper()+'s', sum_amount, sum_cost, sum_fee, aw_price)
        deals.loc[len(deals)] = self.calc_total_results(deals)

        cols = (*RESULTS_COLUMNS[:3], RESULTS_COLUMNS[-1])
        deals_fee = pd.DataFrame(columns=cols)
        for side in ('buy', 'sell'):
            data = self.trades.query(f"side == '{side}'").copy().reset_index(drop=True)[list(RESULTS_COLUMNS)]
            sum_fee = self.round_2(data['fee'].sum())
            if side == 'buy':
                sum_amount = self.round_2(data['amount'].sum())
                sum_cost = self.round_2(data['cost'].sum() + sum_fee)
            else: # 'sell'
                sum_amount = self.round_2(data['amount'].sum() + sum_fee)
                sum_cost = self.round_2(data['cost'].sum())
            aw_price = self.__calc_aw_price(sum_cost, sum_amount) # round((sum_cost / sum_amount), 6)
            deals_fee.loc[len(deals_fee)] = (side.upper()+'s', sum_amount, sum_cost, aw_price)
        deals_fee.loc[len(deals_fee)] = self.calc_total_results(deals_fee)

        self.results = dict(deals=deals, deals_fee=deals_fee)
        return self.results

    def __calc_aw_price(self, sum_cost, sum_amount):
        return round((sum_cost / sum_amount), 6) if sum_amount else 0


    def calc_total_results(self, deals: pd.DataFrame):
        delta_amount = self.round_2(deals['amount'][0] - deals['amount'][1])
        delta_cost = self.round_2(deals['cost'][0] - deals['cost'][1])
        delta_price = round(delta_cost / delta_amount, 6)
        if 'fee' in deals.columns:
            result_row = ('RESULTs', delta_amount, delta_cost, '', delta_price)
        else:
            result_row = ('RESULTs', delta_amount, delta_cost, delta_price)
        return result_row


    def get_conclusion(self, deals: pd.DataFrame) -> str:
        """
        На вход подаю Агрегированнцю таблицу результатов Торговли
        Средняя Цена покупки: {price_delta}' - ????
        """
        base_coin, quote_coin = self.symbol.upper().split('/')
        res_amount = deals['amount'][2]
        res_cost = deals['cost'][2]
        # res_price = deals['price'][2]
        message = 'Продано' if res_amount < 0 else 'Куплено'
        amount_message =  message + f" {base_coin}: {abs(res_amount)} | "
        message = 'Приобретено' if res_cost < 0 else 'Потрачено'
        cost_message = message + f" {quote_coin}: {abs(res_cost)} | "
        turnover_amount = deals['amount'][:2].min()
        turnover_message = f"Полный Оборот {base_coin} (на круг): {turnover_amount}"
        return amount_message + cost_message + turnover_message

    def record_bd_results(self, start_date: date, end_date: date):
        """
        self.results = (deals: pd.DataFrame, deals_fee: pd.DataFrame)
        account, trade_symbol, deals, deals_fee, start_date, end_date
        Запись результатов сделок в Базу данных
        """
        if (not self.trade_account) or (not self.symbol) or (not self.results): return
        # for row, row_fee in zip(self.results['deals'].iterrows(), self.results['deals_fee'].iterrows()):
        # row[1]['side']
        with sq.connect(self.database) as connect:
            curs = connect.cursor()
            for (i, row), (i_fee, row_fee) in zip(self.results['deals'].iterrows(), self.results['deals_fee'].iterrows()):
                curs.execute(f"""INSERT INTO TradeResults
                (account, symbol, side, amount, cost, price, fee, amount_fee, cost_fee, price_fee, start_date, end_date) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",(
                    self.trade_account,
                    self.symbol,
                    row['side'],
                    row['amount'],
                    row['cost'],
                    row['price'],
                    row['fee'],
                    row_fee['amount'],
                    row_fee['cost'],
                    row_fee['price'],
                    start_date,
                    end_date
                  ))


if __name__ == '__main__':

    from Connector.logs import fprint
    from DataBase.path_to_base import TEST_DB

    div_line = '-' * 120
    pd.options.display.width = None  # Отображение Таблицы на весь Экран
    pd.options.display.max_columns = 20  # Макс Кол-во Отображаемых Колонок
    pd.options.display.max_rows = 30  # Макс Кол-во Отображаемых Cтрок

    DB = TEST_DB
    SYMBOL = 'DUSD/USDT'
    ACCOUNT = 'TEST_Luchnik'


    # Инициализация
    accounts = Accounts(DB)

    # Подключение к Аккаунту
    accounts.set_trade_account(ACCOUNT)
    # accounts.exchange.set_test_mode(True) # Тестовый режим
    fprint('Account:', ACCOUNT, accounts.exchange)

    # Таблица Баланса
    balance = accounts.get_balance()
    fprint('Balance:', balance)

    # Таблица Стоимости в USDT Баланса
    cost_balance = accounts.get_cost_balanse()
    fprint('Cost Balance:', cost_balance)

    # Таблица Ордеров. Отдельно SELL отдельно BUY
    orders = accounts.get_open_orders()
    fprint('SELL Orders', orders.query("side == 'sell'"))
    fprint('BUY Orders', orders.query("side == 'buy'"))

    # Таблица Сделок
    trades = accounts.get_trades(symbol=SYMBOL, startTime='2024-03-22', endTime='2024-03-23')
    fprint('TRADES:', trades)

    # Результаты Торговли
    result_deals = accounts.get_trade_results()
    deals = result_deals['deals']
    deals_fee = result_deals['deals_fee']
    conclusion = accounts.get_conclusion(deals)
    conclusion_fee = accounts.get_conclusion(deals_fee)
    fprint('RESULTS: (excluding Fee)', deals, conclusion, div_line, 'RESULTS: (including Fee)', deals_fee, conclusion_fee)

    # Запись Результатов Торговли в Базу Данных - Результат работы см мв Базе Данных
    # accounts.record_bd_results(start_date=date(2024,3,4), end_date=date(2024,3,7))
