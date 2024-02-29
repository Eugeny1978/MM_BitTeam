import streamlit as st
from Interface.accounts import Accounts, make_style_df
from DataBase.path_to_base import TEST_DB, DATABASE
from datetime import date, timedelta, time, datetime

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

with tabs[2]:
    with st.form('Trade FORM', clear_on_submit=False, border=False):
        st.markdown('Trades:')
        colA, colB = st.columns([1, 5])
        with colA:
            submitted = st.form_submit_button("Get Trades")
            today = date.today()
            default_date = today - timedelta(days=7) # weeks=1
            start_date = st.date_input('from:', value=default_date, max_value=today) # format="YYYY.MM.DD" / 00:00 время
            end_date = st.date_input('to:', max_value=today) + timedelta(days=1) # добавляю сутки
            # t = st.time_input('Time:', value="now", step=timedelta(minutes=5)) # int = secundes = 900 = 15 minutes
            # st.write(start_date.ctime())
            # st.write(end_date.ctime())
        with colB:
            st.dataframe(trades.style.pipe(make_style_df), use_container_width=True)



tabs[3].markdown('Results:')
# tabs[3].dataframe(trades)


# График Агрегированный по процентам
# Результат Торговли
