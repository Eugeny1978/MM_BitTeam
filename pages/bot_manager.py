import streamlit as st
import sqlite3 as sq
from datetime import datetime
from DataBase.path_to_base import TEST_DB

# В терминале набрать: streamlit run app.py

DATABASE = TEST_DB
RADIO_OPTIONS: tuple = ('Run', 'Pause', 'Stop')
FORMAT_dt = '%Y-%m-%d %H:%M:%S'

def get_bot_names():
    with sq.connect(DATABASE) as connect:
        curs = connect.cursor()
        curs.execute(f"SELECT name FROM Bots")
        return [row[0] for row in curs]

def get_index_state(bot_name):
    with sq.connect(DATABASE) as connect:
        curs = connect.cursor()
        curs.execute(f"SELECT state FROM Bots WHERE name IS '{bot_name}'")
        responce = curs.fetchone()[0]
        if not responce or responce == 'None' or responce == "NULL": return None
        return RADIO_OPTIONS.index(responce)

def update_bot_states(bots, states):
    with sq.connect(DATABASE) as connect:
        curs = connect.cursor()
        for bot, state in zip(bots, states):
            if state == None: state = 'Stop'
            curs.execute(f"UPDATE Bots SET state = '{state}' WHERE name IS '{bot}'")

def set_states_all_bots(bots, state):
    # Цикл необходим тк иначе последнее изменение не отрабатывает Если менялось 1 раз
    for key in bots:
        st.session_state[key] = state
    with sq.connect(DATABASE) as connect:
        curs = connect.cursor()
        for bot in bots:
            curs.execute(f"UPDATE Bots SET state = '{state}' WHERE name IS '{bot}'")
    print_message(state)

def get_dt_now():
    dt_now = datetime.now()
    dt_str = dt_now.strftime(FORMAT_dt)
    return dt_str

def print_message(state: str):
    text = ''
    if state == RADIO_OPTIONS[0]:
        text = 'Запущены ВСЕ Боты'
    elif state == RADIO_OPTIONS[1]:
        text = 'ВСЕ Боты поставлены на ПАУЗУ'
    elif state == RADIO_OPTIONS[2]:
        text = 'Остановлены ВСЕ Боты'
    st.write(f'{text} | {get_dt_now()}')

# ЛОГИКА СТРАНИЦЫ

st.set_page_config(layout="wide") # Вся страница вместо узкой центральной колонки

st.header('Менеджер Ботов', anchor=False, divider='red')

bot_names = get_bot_names()
columns = st.columns(len(bot_names))
buttons = []
for bot, column in zip(bot_names, columns):
    name = 'Bot_' + bot
    with column:
        button = column.radio(name, options=RADIO_OPTIONS, index=get_index_state(bot), key=bot)
    buttons.append(button)

# colA, colB, colC, colD, colE = st.columns((1, 1, 1, 1, 6))
colA, colB, colC, colD = st.columns(4)
box = colA.checkbox("Change The Value First", key="box") # , label_visibility='hidden'  disabled=True
run_button = colB.button('All Bots RUN', args=(bot_names, RADIO_OPTIONS[0]), use_container_width=True, on_click=set_states_all_bots)
pause_button = colC.button('All Bots PAUSE', args=(bot_names, RADIO_OPTIONS[1]), use_container_width=True, on_click=set_states_all_bots) #
stop_button = colD.button('All Bots STOP', args=(bot_names, RADIO_OPTIONS[2]), use_container_width=True, on_click=set_states_all_bots)

update_bot_states(bot_names, buttons)
