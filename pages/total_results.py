import streamlit as st
import pandas as pd
from Interface.accounts import Accounts, make_style_df
from DataBase.path_to_base import TEST_DB, DATABASE
from datetime import date, timedelta, time, datetime
from Scripts.total_result_test import calc_total_results

# В терминале набрать: streamlit run app.py

DB =  DATABASE
ACC_1 = 'DUSD_1'
ACC_2 = 'DUSD_2'
SYMBOL = 'DUSD/USDT'
START = '2024-03-25'
END = date.today() + timedelta(days=1)
START_BALANCE_1 = dict(base_coin=40_000, quote_coin=50_000)
START_BALANCE_2 = dict(base_coin=38_900, quote_coin=44_571.27)


# ЛОГИКА СТРАНИЦЫ

st.set_page_config(layout="wide") # Вся страница вместо узкой центральной колонки
st.header(f'Итоговые Результаты по счетам | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}', anchor=False, divider='red')

total_1 = calc_total_results(DB, ACC_1, SYMBOL, START, END, START_BALANCE_1)
total_2 = calc_total_results(DB, ACC_2, SYMBOL, START, END, START_BALANCE_2)

coins = SYMBOL.split('/')
base_coin = coins[0]
quote_coin = coins[1]

total = pd.DataFrame(columns=total_1.columns)
total.loc[base_coin] = total_1.loc[base_coin] + total_2.loc[base_coin]
total.loc[quote_coin] = total_1.loc[quote_coin] + total_2.loc[quote_coin]
total.loc['SUM'] = total.sum()

st.markdown('Results DUSD_1:')
st.dataframe(total_1) # , use_container_width=True
st.caption('---')

st.markdown('Results DUSD_2:')
st.dataframe(total_2)
st.caption('---')

st.markdown('TOTAL Results:')
st.dataframe(total)

