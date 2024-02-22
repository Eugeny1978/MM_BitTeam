from Interface.accounts import Accounts
from DataBase.path_to_base import TEST_DB
import json

div_line = '-'*120
SYMBOL = 'DEL/USDT'

def mprint(data):
    print(json.dumps(data), div_line, sep='\n')


account = 'Constantin'
accounts = Accounts(database=TEST_DB)
accounts.set_trade_account(account)
exchange = accounts.exchange
# exchange.set_test_mode(True)


# book = exchange.fetch_order_book(SYMBOL)
# book_cmc = exchange.fetch_order_book_cmc(SYMBOL)
# mprint(book)
# mprint(book_cmc)

# ticker = exchange.fetch_ticker(SYMBOL)
# tickers = exchange.info_tickers()
# tickers_cmc = exchange.info_tickers_cmc()
# tickers_brief_cmc = exchange.info_tickers_brief_cmc()
# mprint(ticker)
# mprint(tickers)
# mprint(tickers_cmc)
# mprint(tickers_brief_cmc)

# coins = exchange.info_coins()
# mprint(coins)




