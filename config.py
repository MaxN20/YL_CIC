import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.types.input_file import InputFile
from aiogram.utils.deep_linking import get_start_link, decode_payload
from aiogram import executor

company_dict = {'Google': '$', 'Yandex': '₽', 'СБЕР': '₽', 'МТС': '₽', 'Facebook': '$', 'Amazon': '$', 'Тинкофф': '₽', 'Газпром': '₽', 'Альфа-Банк': '₽', 'Skyeng': '₽'}
company_list = list(company_dict.keys())

anon_name = ['krutoi', 'hacker', 'stalker', 'killer', 'anon', 'top', 'boss', 'guest', 'user', 'bot']
anon_end = ['777', '888', '999', 'random', 'random', 'random', '$$$', '_', '*']
hack_work_list = ['Взломать сайт', 'Украсть файлы Cookies', 'Найти уязвимость в системе', 'Создать фишинг сайт', 'Провести DDoS-атаку', 'Провести брутфорс-атаку']
hack_work_dict = dict()

jobs_file = open("Resources/jobs.txt", "r", encoding='utf-8')
jobs_list = []

for job in jobs_file.readlines():
    jobs_list.append(job)
jobs_file.close()


list_of_good_users = set()
emoji_dict = {127922: [[6], 5], 127920: [[64, 43, 22, 1], 40, 5], 127919: [[6], 5], 127936: [[4, 5], 2], 127923: [[6], 5], 9917: [[3, 4, 5], 1.5]}
beta_test_users = []

beta_test_users_file = open("Resources/beta.txt", "r")
beta_test_users_set = set()

for user in beta_test_users_file.readlines():
    beta_test_users_set.add(int(user))
beta_test_users_file.close()

users_games_file = open("Resources/games.txt", "r")
users_games_set = set()

for user in users_games_file.readlines():
    users_games_set.add(int(user))
users_games_file.close()

good_news = ['Поздравлю! Ты выиграл!', 'Удача на твоей стороне!', 'Победа!', 'Удача!', 'Сегодня твой день!']
bad_news = ['Не в этот раз', 'Не повезло', 'Может в другой раз']
moneydict = {'rub': '₽', 'usd': '$', 'ton': 'TON'}

channel_name = '@cat_in_code_beta'

API_TOKEN = 'XXXXXXXXXXX:XXXXXXXXXXXXXXXXXXXXXXXXXXX'
admin_id = 1037575855
admin_balance_flag = 0
admin_user_flag = 0
admin_promo_info_flag = 0
admin_promo_flag = 0
admin_mailing = 0
text_mail = ''
ton_for_sub_flag = 0
list_of_good_users = set()

logging.basicConfig(filename='output.txt', level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

programsdict = dict()

bd_1 = 'user_data.db'
bd_2 = 'programs.db'
bd_3 = 'proms.db'

conn = sqlite3.connect(bd_1)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        telegram_name TEXT,
        energy INTEGER,
        health INTEGER,
        hunger INTEGER,
        status TEXT,
        rep INTEGER,
        ruble REAL,
        dollar REAL,
        toncoin REAL,
        exchange TEXT,
        skill INTEGER,
        computer TEXT,
        flag TEXT
    )
''')
conn.commit()

conn2 = sqlite3.connect(bd_2)
cursor2 = conn2.cursor()
cursor2.execute('''
    CREATE TABLE IF NOT EXISTS programs (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        description TEXT,
        time INTEGER,
        price INTEGER,
        skill INTEGER,
        status TEXT,
        type TEXT,
        currency TEXT
    )
''')
conn2.commit()

conn3 = sqlite3.connect(bd_3)
cursor3 = conn3.cursor()
cursor3.execute('''
    CREATE TABLE IF NOT EXISTS proms (
        name TEXT PRIMARY KEY,
        value INTEGER,
        count INTEGER,
        type TEXT
    )
''')
conn3.commit()    
