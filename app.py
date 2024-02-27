import streamlit as st
from Interface.accounts import Accounts, make_style_df
from DataBase.path_to_base import TEST_DB, DATABASE

# В терминале набрать: streamlit run app.py

# ЛОГИКА СТРАНИЦЫ

st.set_page_config(layout="wide") # Вся страница вместо узкой центральной колонки
st.header('Информация по Счету:', anchor=False, divider='red')

# Поле выбора Аккаунта
accounts = Accounts(TEST_DB)
account = st.selectbox('Account:', index=2, options=accounts.acc_names, placeholder="Choose an account name", key='account') # , on_change=
accounts.set_trade_account(account)

# Таблица Баланса
balance = accounts.get_balance()
# Таблица Стоимости Баланса
cost_balance = accounts.get_cost_balanse()

# Таблица Ордеров. Отдельно SELL отдельно BUY
orders = accounts.get_open_orders()

# Таблица Сделок
trades = accounts.get_trades()

tab_names = ('Balance', 'Orders', 'Trades', 'Results')
tabs = st.tabs(tab_names)

# tabs[0].markdown('Spot Balance:')
# tabs[0].dataframe(balance.style.pipe(make_style_df))
colSpot, colCost = tabs[0].columns(2)
with colSpot:
    st.markdown('Spot Balance:')
    st.dataframe(balance.style.pipe(make_style_df), use_container_width=True)
with colCost:
    st.markdown('Cost Balance:')
    st.dataframe(cost_balance, use_container_width=True)

colSell, colBuy = tabs[1].columns(2)
with colSell:
    st.markdown(':red[SELL Orders:]')
    st.dataframe(orders.query("side == 'sell'").reset_index(drop=True).style.pipe(make_style_df), use_container_width=True) # height=300
with colBuy:
    st.markdown(':green[BUY Orders:]')
    st.dataframe(orders.query("side == 'buy'").reset_index(drop=True).style.pipe(make_style_df), use_container_width=True)

tabs[2].markdown('Trades:')
tabs[2].dataframe(trades.style.pipe(make_style_df))

tabs[3].markdown('Results:')
# tabs[3].dataframe(trades)


# График Агрегированный по процентам
# Результат Торговли
