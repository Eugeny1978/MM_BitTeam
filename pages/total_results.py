import streamlit as st
from Interface.accounts import Accounts, make_style_df
from DataBase.path_to_base import TEST_DB, DATABASE
from datetime import date, timedelta, time, datetime

# В терминале набрать: streamlit run app.py

DB =  DATABASE

# ЛОГИКА СТРАНИЦЫ

st.set_page_config(layout="wide") # Вся страница вместо узкой центральной колонки
st.header('Итоговые Результаты по всем счетам', anchor=False, divider='red')

