import requests                                 # Библиотека для создания и обработки запросов
import sqlite3 as sq                            # Библиотека  Работа с БД
from typing import Literal                      # Создание Классов Перечислений

# Допустимый Формат Написания Торговых Пар (Символов)
# symbol='del_usdt' - родной
# symbol='DEL/USDT' - Унификация с ccxt. Преобразуется в del_usdt

OrderSide = Literal['buy', 'sell']
OrderType = Literal['limit', 'market']
UserOrderTypes = Literal['history', 'active', 'closed', 'cancelled', 'all'] # history = closed + cancelled

class BitTeam(): # Request
    """
    2 Основных Раздела:
    /ccxt - приватные методы
    /cmc - публичные методы
    """
    base_url = 'https://bit.team/trade/api'
    status = None           # Статус-код последнего запроса 200 - если ок
    data = None             # Данные последнего запроса
    auth = None
    __name__ = 'BitTeam'

    def __str__(self):
        return self.__name__

    def __init__(self, account={'apiKey': None, 'secret': None}, ):
        self.account: dict = account
        self.load_markets() # self.markets =

    def set_test_mode(self, mode: bool):
        if not mode:
            self.base_url = 'https://bit.team/trade/api'
        else:
            # self.base_url = 'https://dkr3.bit.team/trade/api'
            self.base_url = 'https://dkr.bit.team/trade/api'
        self.load_markets()

    @staticmethod
    def format_symbol(symbol: str) -> str:
        """
        Привожу Унифицированный Формат к Родному
        """
        return symbol.lower().replace('/', '_')

    @staticmethod
    def format_pair(pair: str) -> str:
        """
        Привожу Родной Формат к Унифицированному
        """
        return pair.upper().replace('_', '/')

    def __request(self, path:str, method:str='get', params={}, data={}):
        """
        # Возможно необходимо прописать Заголовок headers = {'user-agent': 'my-app/0.0.1'}
        :path: Локальный Путь к Конечной Точке
        :method: 'get', 'post'
        :params: payloads = {} Параметры (дополняют url ? &)
        :data: body = {} Тело Запроса
        :return: Возвращает Данные Запроса
        """
        url = (self.base_url + path)
        match method:
            case 'get':
                response = requests.get(url, auth=self.auth, params=params, data=data)
            case 'post':
                response = requests.post(url, auth=self.auth, params=params, data=data)
            case _:
                response = {}
        self.status = response.status_code
        self.data = response.json() # json.dumps(response)

        match self.status: # Проверка Прохождения Запроса
            case 200:
                # Закомментил тк есть нестандартный метод fetch_order_book_cmc
                # if self.data['ok'] and 'result' in self.data:
                #     return self.data
                return self.data
            case _:
                print(f'Статус-Код: {self.status} | {self.data}')
                raise('Запрос НЕ Прошел!')

    def load_markets(self):
        """
        Метод для загрузки id Торговых Пар, Шагов Цен, Объемов, Мин Ордеров по всем торгуемым Парам.
        Как правило Биржа позволяет округлять объем до 8 знаков, цену до 6, мин объем 0.1 USD
        Проверил на DEL/USDT, ETH/USDT - действительно в стакане присутствуют такие цены объемы
        """
        self.info_tickers()
        markets = {}
        for symbol in self.data['result']['pairs']:
            markets[self.format_pair(symbol['name'])] = {
                'id': symbol['id'],
                'baseStep': symbol['baseStep'],
                'quoteStep': symbol['quoteStep'],
                'priceStep': symbol['settings']['price_view_min'],
                'limit_usd': float(symbol['settings']['limit_usd'])
                }
        self.markets = markets
        return self.markets

    def fetch_order_book(self, symbol='del_usdt'):
        """
        Стакан Цен по выбранной Паре.
        Разработчик заявляет о предоставлении ВСЕГО Стакана
        Также Стакан есть и в запросе "pair". Но там он обрезан лимитом в 50 слотов
        """
        symbol = self.format_symbol(symbol)
        return self.__request(path=f'/orderbooks/{symbol}')

    def fetch_order_book_cmc(self, symbol='del_usdt'):
        """
        Стакан Цен по выбранной Паре. Альтернативный вариант.
        Разработчик заявляет о предоставлении ВСЕГО Стакана
        Возвращает Ответ в нестандартной для Текущего API структуре (см. docs_bitteam).
        Возможно, отрабатыет быстрее чем fetch_order_book(symbol)
        """
        symbol = self.format_symbol(symbol)
        return self.__request(path=f'/cmc/orderbook/{symbol}')

    def fetch_common_trades(self, symbol='del_usdt'):
        """
        Недавно (скорее всего за 24 часа) завершенные сделки для данного Ticker-a
        """
        symbol = self.format_symbol(symbol)
        return self.__request(path=f'/cmc/trades/{symbol}')

    def fetch_ticker(self, symbol='del_usdt'):
        """
        Информация по Торговой Паре за 24 часа.
        Весь Стакан есть и в запросе "orderbooks". Здесь он обрезан лимитом в 50 слотов
        # Мин. шаг размера Лота. Кол-во знаков в Дроби после целой части. int()
        print(f"Шаг Размера Лота: {self.date['result']['pair']['baseStep']}")
        # Кол-во знаков в Дроби после целой части. str()
        print(f"ЦЕНА. Кол-во Знаков после целой части: {self.date['result']['pair']['settings']['price_view_min']}")
        # Кол-во знаков в Дроби после целой части. str()
        print(f"Размер Позы. Кол-во Знаков после целой части: {self.date['result']['pair']['settings']['lot_size_view_min']}")
        # Мин. размер Лота относительно Доллара US. str()
        print(f"Мин. Размер Позы в USD: {self.date['result']['pair']['settings']['limit_usd']}")
        """
        symbol = self.format_symbol(symbol)
        return self.__request(path=f'/pair/{symbol}')

    def info_tickers(self):
        """
        Информация по ВСЕМ Торгуемым на Бирже Парам за 24 часа.
        Использую Пи инициализации для получения Словаря "markets". Шаги Цен, Объемов, Мин Объем Ордеров, ID Торг Пар
        """
        return self.__request(path='/pairs')

    def info_tickers_cmc(self):
        """
        Информация по ВСЕМ Торгуемым на Бирже Парам за 24 часа.
        Альтернативный метод.
        """
        return self.__request(path=f'/cmc/summary')

    def info_tickers_brief_cmc(self):
        """
        Информация по ВСЕМ Торгуемым на Бирже Парам за 24 часа.
        Альтернативный метод. Лаконичные сведения.
        Последняя Цена и Суточные Объемы
        """
        return self.__request(path=f'/cmc/ticker')

    def info_coins(self):
        """
        Общая Информация о Криптовалютах (Coin-ах), доступных на бирже
        У некоторых Валют отсутствуюи поля: maker_fee, taker_fee (см. docs)
        """
        return self.__request(path=f'/cmc/assets')


# --- ПРИВАТНЫЕ ЗАПРОСЫ. Требуется Предварительная Авторизация -----------------------------

    def authorization(self):
        if (not self.account['apiKey']) or (not self.account['secret']):
            print('Ошибка Авторизации. Задайте/Проверьте Публичный и Секретный АПИ Ключи')
            raise
        basic_auth = requests.auth.HTTPBasicAuth(self.account['apiKey'], self.account['secret'])
        self.auth = basic_auth

    def fetch_balance(self):
        """
        Полный Баланс По Спот Аккаунту
        """
        if not self.auth: self.authorization()
        return self.__request(path=f'/ccxt/balance') # Был Убран ['result']

    def __get_pairId_markets(self, symbol):
        return self.markets[symbol]['id']

    def create_order(self, symbol: str, type: OrderType, side: OrderSide, amount: float, price: float=0):
        """
        Привести к Виду:
        body = {'pairId':   str, #  '24' del_usdt
                'side':     str, # "buy", "sell"
                'type':     str, # "limit", "market"
                'amount':   str, # '330' (value in coin1 (farms))
                'price':    str  # '0.04' (price in base coin (usdt))
                }
        """
        if not self.auth: self.authorization()
        pairId = self.__get_pairId_markets(symbol)
        body = {'pairId': pairId,
                'side': side,
                'type': type,
                'amount': str(amount) # округлить до 6 знаков str(round(amount, 6))?
                }
        if type == 'limit':
            body['price'] = str(price) # округлить до 6 знаков str(round(price, 6))?
        return self.__request(path='/ccxt/ordercreate', method='post', data=body)

    def cancel_order(self, id: (int, str)):
        """
        cancel_order(self, id: str, symbol: Optional[str] = None, params={}) # ccxt
        id_order = data['result']['id'] # create_order(body)
        """
        if not self.auth: self.authorization()
        body = {"id": id}
        return self.__request(path='/ccxt/cancelorder', method='post', data=body)

    def cancel_all_orders(self, symbol=None):
        """
        cancel_all_orders(self, symbol: Optional[str] = None, params={}) # ccxt
        pairId 1-100 - по конкретной паре || 0 - all pairs | 24 - del_usdt
        """
        if not self.auth: self.authorization()
        if symbol:
            pairId = self.__get_pairId_markets(symbol)
        else:
            pairId = 0
        body = {"pairId": pairId}
        self.__request(path='/ccxt/cancel-all-order', method='post', data=body)
        if pairId:
            print(f'BitTeam. Удалены Все Ордера по Символу: {symbol}')
        else:
            print(f'BitTeam. Удалены ВСЕ Ордера')
        return self.data

    def fetch_order(self, order_id: (int or str)):
        """
        # fetch_order(self, id: str, symbol: Optional[str] = None, params={})  # ccxt
        Информация об Ордере по его ID
        """
        if not self.auth: self.authorization()
        return self.__request(path=f'/ccxt/order/{order_id}')

    def fetch_orders(self, symbol=None, limit=10_000, type:UserOrderTypes='active', offset=0, order={}, where=''):
        """
        /trade/api/ccxt/ordersOfUser?limit=10&offset=0&order[timestamp]=DESC&order[price]=ASC&pair=btc_usdt&where[pairId]=5&type=all
        fetch_orders(self, symbol: Optional[str] = None, since: Optional[int] = None, limit: Optional[int] = None, params={})
        Ордера за Текущую Дату
        symbol - Фильтр по Символу
        limit - Макс Кол-во выводимых ордеров
        type= 'history', 'active', 'closed', 'cancelled', 'all'| history = closed + cancelled  - Вид Ордера
        offset=х - смещение: не покажет первые Х ордеров
        order: Упорядычевание. По умолчанию 'order[timestamp]'='DESC' обратный от Позних к Ранним. 'ASC' - Прямой порядок
        Допустимые Колонки: (Формирование Словаря см в методе __form_order_by(order))
            'timestamp': 'DESC',
            'price': 'ASC',
            'side': 'ASC',
            'type': 'ASC',
            'executed': 'ASC',
            'executedPrice': 'ASC'
            Тесты 2024.02.28 показали что реально отрабатывает только сортировка по времени
        where='' - Альтернативный Способ фильтра по Символу (изначально по его Id)
        """
        if not self.auth: self.authorization()
        payloads = {
            'limit': limit,
            'type': type,
            'offset': offset,
            }
        if symbol: # фильтр по Символу
            payloads['pair'] = self.format_symbol(symbol)
        if where and not symbol: # альтернативный фильтр по Символу
            payloads['where[pairId]'] = self.__get_pairId_markets(where)
        if len(order):
            order_payloads = self.__form_order_by(order)
            payloads = payloads | order_payloads
        self.__request(path=f'/ccxt/ordersOfUser', params=payloads)
        return self.data

    @staticmethod
    def __form_order_by(order: dict) -> dict:
        valid_keys = ('timestamp', 'price', 'side', 'type', 'executed', 'executedPrice')
        formatted_order = {}
        for key, value in order.items():
            if key in valid_keys:
                f_key = f"order[{key}]"
                formatted_order[f_key] = value
            else:
                print(f"Не корректная Попытка указать порядок вывода Ордеров. | Ключ '{key}' НЕ Актуален")
        return formatted_order

    def fetch_my_trades(self, symbol=0, limit=10_000, offset=0, order={}):
        """
        Тесты показали Максимально: Сделки за Последние 3 дня (устанавливал лимит 1000)
        offset=х - смещение: не покажет первые Х сделок
        pairId=0 - все пары # 24 - del_usdt
        Сортировка
        Допустимые Колонки: (Формирование Словаря см в методе __form_order_by(order))
            'timestamp': 'DESC',
            'price': 'ASC',
            'side': 'ASC',
            'type': 'ASC',
            'executed': 'ASC',
            'executedPrice': 'ASC'
            Тесты 2024.02.28 показали что реально не отрабатывает ни одна сортировка
        /trade/api/ccxt/tradesOfUser?order[timestamp]=ASC&limit=20
        ccxt/tradesOfUser?limit=10&offset=0&order=<string>&pairId=<integer>
        ccxt:
        fetch_my_trades(self, symbol: Optional[str] = None, since: Optional[int] = None, limit: Optional[int] = None, params={}):
        """
        if not self.auth: self.authorization()
        payloads = {
            'limit': limit,
            'offset': offset,
        }
        if symbol:
            payloads['pairId'] = self.__get_pairId_markets(symbol)
        if len(order):
            order_payloads = self.__form_order_by(order)
            payloads = payloads | order_payloads
        return self.__request(path=f'/ccxt/tradesOfUser', params=payloads)


if __name__ == '__main__':

    from DataBase.path_to_base import TEST_DB
    import json

    div_line = '-' * 120
    SYMBOL = 'ETH/USDT'
    SYMBOL_TEST = 'DUSD/USDT'

    def jprint(data):
        print(json.dumps(data), div_line, sep='\n')

    def mprint(*args):
        print(*args, div_line, sep='\n')

    def is_test_trade_mode(mode: str) -> bool:
        return True if mode == 'Test' else False

    def get_data_from_db(account, database):
        """
        Данные по Аккаунту из Базы Данных
        """
        try:
            with sq.connect(database) as connect:
                # connect.row_factory = sq.Row
                curs = connect.cursor()
                curs.execute(f"SELECT apiKey, secret, mode FROM Accounts WHERE name IS '{account}'")
                responce = curs.fetchone()
                return dict(apiKey=responce[0], secret=responce[1]), is_test_trade_mode(responce[2])
        except Exception as error:
            print('Нет Доступа к базе | Проверь также имя Аккаунта.')
            raise (error)

    acc_name = 'Constantin'
    acc_name__test = 'TEST_Korolev'

    # # Инициализация
    connect = BitTeam()

    # # ПУБЛИЧНЫЕ ЗАПРОСЫ ------------------

    # # Markets
    # jprint(connect.markets)
    # jprint(connect.load_markets())

    # # order_book
    # jprint(connect.fetch_order_book())
    # jprint(connect.fetch_order_book(SYMBOL))
    # jprint(connect.fetch_order_book_cmc())
    # jprint(connect.fetch_order_book_cmc(SYMBOL))

    # # common_trades
    # jprint(connect.fetch_common_trades())
    # jprint(connect.fetch_common_trades(SYMBOL))

    # # ticker
    # jprint(connect.fetch_ticker())
    # jprint(connect.fetch_ticker(SYMBOL))

    # # tickers / coins
    # jprint(connect.info_tickers())
    # jprint(connect.info_tickers_cmc())
    # jprint(connect.info_tickers_brief_cmc())
    # jprint(connect.info_coins())

    # # ПРИВАТНЫЕ ЗАПРОСЫ ------------------

    # # Данные по Аккаунту из Базы Данных
    # acc_keys, acc_mode = get_data_from_db(acc_name, TEST_DB)
    acc_keys, acc_mode = get_data_from_db(acc_name__test, TEST_DB)

    # mprint(acc_keys, acc_mode)

    # # Варианты Авторизации
    # # Авторизация Сразу при Инициализации:
    # connect = BitTeam(acc_keys)
    # # Если ранее соединение было и теперь необходимо только авторизация
    connect.account = acc_keys

    # Если Работаем на Тестовом Сервере (Включаем - Тестовый Режим - Меняется отсновной URL)
    # Для Реальной Торговли не обязательно. Тк по умолчанию запросы уходят туда.
    connect.set_test_mode(acc_mode)

    # # Должны обновиться markets (тк для разных режимов есть отличия)
    # jprint(connect.markets)

    # # balance
    # jprint(connect.fetch_balance())

    # # create_order
    # order = connect.create_order(symbol=SYMBOL_TEST, type= 'limit', side='sell', amount = 100, price = 1.1)
    # order = connect.create_order(symbol=SYMBOL, type= 'limit', side='sell', amount = 1, price = 4000)
    # jprint(order)

    # # fetch_order
    # id = 275785245
    # my_order = connect.fetch_order(order_id=id)
    # my_order = connect.fetch_order(order_id=str(id))
    # jprint(my_order)

    # # fetch_orders
    # my_orders = connect.fetch_orders()
    # my_orders = connect.fetch_orders(order='ASC')
    # my_orders = connect.fetch_orders(limit=5)
    # my_orders = connect.fetch_orders(offset=4)
    # my_orders = connect.fetch_orders(type='history')
    # # my_orders = connect.fetch_orders(where='timestamp > 1709021936') # ТАК НЕЛЬЗЯ только фильтр по символу по pairId см. описание
    # # my_orders = connect.fetch_orders(where='price > 1.01') # ТАК НЕЛЬЗЯ
    # my_orders = connect.fetch_orders(symbol=SYMBOL_TEST)
    # my_orders = connect.fetch_orders(where=SYMBOL_TEST) # альтернативно
    # order_by = {'price': 'ASC'} # не сортирует
    # my_orders = connect.fetch_orders(order=order_by)
    # order_by = {'side': 'ASC'} # не сортирует
    # my_orders = connect.fetch_orders(order=order_by)
    order_by = {'timestamp': 'ASC'} # Сортирует
    my_orders = connect.fetch_orders(order=order_by)
    jprint(my_orders)

    # # cancel_order
    # id1 = 275785245 #
    # response = connect.cancel_order(id=id1)
    # id2 = str(275785201)  # можно также и строкой
    # response = connect.cancel_order(id2)
    # jprint(response)

    # # cancel_all_orders
    # response = connect.cancel_all_orders(symbol=SYMBOL)
    # response = connect.cancel_all_orders()
    # jprint(response)

    # # fetch_my_trades Сделать Сделки и Проверить! либо проверить на Реальном Акке где были сделки (жду когда поправят лимить)
    # # (symbol=0, limit=10_000, offset=0, order='DESC')
    # trades = connect.fetch_my_trades()
    # trades = connect.fetch_my_trades(symbol=SYMBOL_TEST)
    # trades = connect.fetch_my_trades(limit=5)
    # trades = connect.fetch_my_trades(offset=2)

    # order_by = {'price': 'ASC'} # не сортирует
    # trades = connect.fetch_my_trades(order=order_by)
    # order_by = {'side': 'ASC'} # не пробовал
    # trades = connect.fetch_my_trades(order=order_by)
    # order_by = {'timestamp': 'ASC'} # не сортирует
    # trades = connect.fetch_my_trades(order=order_by)
    # jprint(trades)

