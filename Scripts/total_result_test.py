from Interface.accounts import Accounts
import pandas as pd

def rround(value):
    return round(value, 2)

def calc_total_results(database, account_name, symbol, trade_start, trade_end, start_balance):

    acc = Accounts(database)
    acc.set_trade_account(account_name)
    balance = acc.get_balance()
    trades = acc.get_trades(symbol=symbol, startTime=trade_start, endTime=trade_end)
    results = acc.get_trade_results()['deals']

    coins = symbol.split('/')
    base_coin = coins[0]
    quote_coin = coins[1]
    columns = ['start_balance', 'temp_balance', 'delta_balance', 'trading', 'fee', 'delta']

    total = pd.DataFrame(columns=columns)
    bcoin_start = rround(start_balance['base_coin'])
    bcoin_temp = rround(balance[base_coin]['total'])
    bcoin_delta_balance = rround(bcoin_temp - bcoin_start)
    bcoin_trading = rround(results.query("side == 'RESULTs'")['amount'].values[0])
    bcoin_fee = rround(results.query("side == 'BUYs'")['fee'].values[0])
    bcoin_delta = rround(bcoin_delta_balance - (bcoin_trading - bcoin_fee))

    qcoin_start = rround(start_balance['quote_coin'])
    qcoin_temp = rround(balance[quote_coin]['total'])
    qcoin_delta_balance = rround(qcoin_temp - qcoin_start)
    qcoin_trading = -rround(results.query("side == 'RESULTs'")['cost'].values[0])
    qcoin_fee = rround(results.query("side == 'SELLs'")['fee'].values[0])
    qcoin_delta = rround(qcoin_delta_balance - (qcoin_trading - qcoin_fee))

    total.loc[base_coin] = (
        bcoin_start,
        bcoin_temp,
       bcoin_delta_balance,
       bcoin_trading,
       bcoin_fee,
       bcoin_delta)
    total.loc[quote_coin] = (
        qcoin_start,
        qcoin_temp,
        qcoin_delta_balance,
        qcoin_trading,
        qcoin_fee,
        qcoin_delta)

    # fprint('Temp Balance:', balance)
    # fprint('Trades:', trades)
    # fprint('Deals:', results)
    # fprint(f'{account_name}:', total)
    return total



if __name__ == '__main__':

    from Connector.logs import fprint
    from DataBase.path_to_base import DATABASE
    from datetime import date, timedelta
    import pandas as pd

    div_line = '-' * 120
    pd.options.display.width = None  # Отображение Таблицы на весь Экран
    pd.options.display.max_columns = 20  # Макс Кол-во Отображаемых Колонок
    pd.options.display.max_rows = 30  # Макс Кол-во Отображаемых Cтрок

    DB = DATABASE
    ACC_1 = 'DUSD_1'
    ACC_2 = 'DUSD_2'
    SYMBOL = 'DUSD/USDT'
    START = '2024-03-25'
    END = date.today() + timedelta(days=1)
    START_BALANCE_1 = dict(base_coin=40_000, quote_coin=50_000)
    START_BALANCE_2 = dict(base_coin=38_900, quote_coin=44_571.27)

    total_1 = calc_total_results(DB, ACC_1, SYMBOL, START, END, START_BALANCE_1)
    total_2 = calc_total_results(DB, ACC_2, SYMBOL, START, END, START_BALANCE_2)

    coins = SYMBOL.split('/')
    base_coin = coins[0]
    quote_coin = coins[1]

    total = pd.DataFrame(columns=total_1.columns)
    total.loc[base_coin] = total_1.loc[base_coin] + total_2.loc[base_coin]
    total.loc[quote_coin] = total_1.loc[quote_coin] + total_2.loc[quote_coin]
    # total.loc['SUM'] = total.loc[base_coin] + total.loc[quote_coin]
    total.loc['SUM'] = total.sum()
    fprint('TOTAL:', total)








