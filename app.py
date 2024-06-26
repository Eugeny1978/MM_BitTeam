import streamlit as st
from Interface.accounts import Accounts, make_style_df
from DataBase.path_to_base import TEST_DB, DATABASE
from datetime import date, timedelta, time, datetime

# В терминале набрать: streamlit run app.py

DB =  DATABASE

# ЛОГИКА СТРАНИЦЫ

st.set_page_config(layout="wide") # Вся страница вместо узкой центральной колонки
st.header('Информация по Счету:', anchor=False, divider='red')

col_account, col_symbol = st.columns([5,1])

with col_account:
    # Поле выбора Аккаунта
    accounts = Accounts(DB)
    account = st.selectbox('Account:', index=2, options=accounts.acc_names, placeholder="Choose an account name", key='account') # , on_change=
    accounts.set_trade_account(account)
with col_symbol:
    # Поле выбора Торгового Символа
    symbols = ('DEL/USDT', 'DUSD/USDT')
    trade_symbol = st.selectbox('Symbol:', index=1, options=symbols, placeholder="Choose an trade symbol", key='symbol')

tab_names = ('Balance', 'Orders', 'Trades', 'Results')
tabs = st.tabs(tab_names)

with tabs[0]:
    colSpot, colCost = st.columns(2)
    with colSpot:
        # Таблица Баланса
        balance = accounts.get_balance()
        st.markdown('Spot Balance:')
        st.dataframe(balance.style.pipe(make_style_df), use_container_width=True)
    with colCost:
        # Таблица Стоимости Баланса
        cost_balance = accounts.get_cost_balanse()
        st.markdown('Cost Balance:')
        st.dataframe(cost_balance, use_container_width=True)

with tabs[1]:
    colSell, colBuy = st.columns(2)
    # Таблица Ордеров. Отдельно SELL отдельно BUY
    orders = accounts.get_open_orders()
    with colSell:
        sell_orders = orders.query("side == 'sell'").reset_index(drop=True)
        st.markdown(f':red[SELL Orders: | numbers: {len(sell_orders)}]')
        st.dataframe(sell_orders.style.pipe(make_style_df), use_container_width=True) # height=300
    with colBuy:
        buy_orders = orders.query("side == 'buy'").reset_index(drop=True)
        st.markdown(f':green[BUY Orders: | numbers: {len(buy_orders)}]')
        st.dataframe(buy_orders.style.pipe(make_style_df), use_container_width=True)

with tabs[2]:
    with st.form('Trade FORM', clear_on_submit=False, border=False):
        st.markdown('Trades:')
        colA2, colB2 = st.columns([1, 5])
        with colA2:
            submitted = st.form_submit_button("Get Trades")
            today = date.today()
            default_date = today # - timedelta(days=1) # weeks=1
            start_date = st.date_input('from:', value=default_date, max_value=today) # format="YYYY.MM.DD" / 00:00 время
            end_date = st.date_input('to:', max_value=today) + timedelta(days=1) # добавляю сутки
            # t = st.time_input('Time:', value="now", step=timedelta(minutes=5)) # int = secundes = 900 = 15 minutes
        with colB2:
            # Таблица Сделок
            trades = accounts.get_trades(symbol=trade_symbol, startTime=start_date, endTime=end_date)
            # trades = accounts.get_trades(symbol=trade_symbol)
            # Исключение StreamlitAPIException: Фрейм данных содержит 344220 ячеек, но максимальное количество ячеек,
            # разрешенное для рендеринга Pandas Styler, настроено на 262144. Чтобы разрешить стилизацию большего количества ячеек,
            # вы можете изменить конфигурацию "style.render.max_elements". Например: pd.set_option("styler.render.max_elements", 344220)
            st.dataframe(trades, use_container_width=True) # .style.pipe(make_style_df)

with tabs[3]: # Результат Торговли
    results = accounts.get_trade_results()
    deals = results['deals']
    deals_fee = results['deals_fee']
    colA3, colB3 = st.columns(2)
    with colA3:
        st.markdown('RESULTS: (excluding Fee)')
        st.dataframe(deals.style.pipe(make_style_df), use_container_width=True)
        st.markdown(accounts.get_conclusion(deals))
    with colB3:
        st.markdown('RESULTS: (including Fee)')
        st.dataframe(deals_fee.style.pipe(make_style_df), use_container_width=True)
        st.markdown(accounts.get_conclusion(deals_fee))
    record_db = st.button('Record Results in DataBase', args=(start_date, end_date), use_container_width=False, on_click=accounts.record_bd_results) #

