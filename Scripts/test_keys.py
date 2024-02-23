from Interface.accounts import Accounts
from DataBase.path_to_base import TEST_DB
import json

div_line = '-'*120
SYMBOL = 'ETH/USDT'

def jprint(data):
    print(json.dumps(data), div_line, sep='\n')
def dfprint(*args):
    print(*args, div_line, sep='\n')


account = 'TEST_Korolev'
accounts = Accounts(database=TEST_DB)
accounts.set_trade_account(account)
exchange = accounts.exchange
exchange.set_test_mode(True)

book = exchange.fetch_order_book(SYMBOL)
jprint(book)
balance = accounts.get_balance()
dfprint(accounts.trade_account, balance)

account1 = 'TEST_Luchnik'
accounts1 = Accounts(database=TEST_DB)
accounts1.set_trade_account(account1)
exchange1 = accounts1.exchange
exchange1.set_test_mode(True)

balance1 = accounts1.get_balance()
dfprint(accounts1.trade_account, balance1)


