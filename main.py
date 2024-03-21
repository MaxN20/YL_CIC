import logging
import sqlite3
import random
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.types.input_file import InputFile
from aiogram.utils.deep_linking import get_start_link, decode_payload
from aiogram import executor
import asyncio
import aioschedule
import requests
from Resources.food_shop import food_products
from Resources.health_shop import health_products
from Resources.technic_shop import technic_products
from Resources.skill_shop import skill_products
from config import company_dict, company_list, anon_name, anon_end, hack_work_list, hack_work_dict
from config import jobs_file, jobs_list, list_of_good_users, emoji_dict, beta_test_users
from config import beta_test_users_file, beta_test_users_set, users_games_file, users_games_set
from config import good_news, bad_news, moneydict, channel_name
from config import admin_id, admin_balance_flag, admin_user_flag, admin_promo_flag, admin_promo_info_flag, admin_mailing, text_mail, ton_for_sub_flag, list_of_good_users, programsdict
from config import API_TOKEN, bot, dp
from config import bd_1, bd_2, bd_3, conn, cursor, conn2, cursor2, conn3, cursor3  
from administrator import admin
from market import shop
from exchanger import process_exchange_money
import json
import requests
from deep_translator import GoogleTranslator


async def check_work(user_id, callback_query):
    if cursor2.execute("SELECT user_id FROM programs WHERE user_id = ?", (user_id,)).fetchone() != None:
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("📋Перейти к задаче", callback_data=f"program_status:{user_id}")  ,          
            InlineKeyboardButton("🖼Перейти в профиль", callback_data=f"profile:{user_id}")
            )        
        await bot.send_message(user_id, "<b>📌У вас уже есть активная задача</b>", reply_markup=keyboard, parse_mode='html')
        await bot.delete_message(user_id, callback_query.message.message_id)        
        return True

async def check_life(user_id, callback_query):
    if cursor.execute("SELECT status FROM users WHERE user_id = ?", (user_id,)).fetchone()[0] == 'выбыл':
        await bot.send_message(user_id, "<b>📌Ваш персонаж мёртв, начните новую игру:\n\nНажмите: /start</b>", parse_mode='html')
        await bot.delete_message(user_id, callback_query.message.message_id)        
        return True

async def check_all_values(user_id):
    cursor.execute("UPDATE users SET hunger = 100 WHERE user_id = ? AND hunger > 100", (user_id,))
    cursor.execute("UPDATE users SET energy = 100 WHERE user_id = ? AND energy > 100", (user_id,))
    cursor.execute("UPDATE users SET health = 100 WHERE user_id = ? AND health > 100", (user_id,))
    
    cursor.execute("SELECT user_id FROM users WHERE user_id = ? AND health <= 0", (user_id,))
    result = cursor.fetchone() 
    if cursor.fetchone() != None:
        cursor.execute("UPDATE users SET status = 'выбыл', flag = None WHERE user_id = ?", (user_id,))
        users_games_set.discard(user_id)
        await bot.send_message(user_id, "<b>😔Ваш персонаж погиб, вы можете начать новую игру /start</b>", parse_mode='html')
    conn.commit()

async def decrease_hunger():
    cursor.execute("UPDATE users SET hunger = hunger - 1 WHERE hunger > 0")
    cursor.execute("UPDATE users SET health = health - 5 WHERE health > 0 AND hunger = 0")
    conn.commit()
    
    cursor.execute("SELECT user_id FROM users WHERE hunger = 20")
    hunger20_users = cursor.fetchall()

    for user_id in hunger20_users:
        user_id = user_id[0]
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton("🛍Перейти в магазин", callback_data=f"shop:{user_id}"))
        await bot.send_message(user_id, "<b>🤤Ваш персонаж голоден, вам стоит его покормить</b>", reply_markup=keyboard, parse_mode='html')    
    
    cursor.execute("SELECT user_id FROM users WHERE health <= 0 AND status != 'выбыл'")
    dead_users = cursor.fetchall()

    for user_id in dead_users:
        user_id = user_id[0]
        cursor.execute("UPDATE users SET status = 'выбыл', flag = 'None' WHERE user_id = ?", (user_id,))
        users_games_set.discard(user_id)
        await bot.send_message(user_id, "<b>😔Ваш персонаж погиб от голода, вы можете начать новую игру /start</b>", parse_mode='html')
    conn.commit()

async def sleep():
    cursor.execute("SELECT user_id FROM users WHERE status = ?", ('спит',))
    sleep_users = cursor.fetchall()
    for user_id in sleep_users:
        user_id = user_id[0]
        cursor.execute("UPDATE users SET energy = energy + 1 WHERE user_id = ?", (user_id,))
        await check_all_values(user_id)
    conn.commit()
        
async def work():
    cursor.execute("SELECT user_id FROM users WHERE status != ? AND status != ? AND status != ?", ('спит', 'бездельничает', 'выбыл'))
    work_users = cursor.fetchall()
    for user_id in work_users:
        user_id = user_id[0]
        cursor.execute("SELECT energy FROM users WHERE user_id = ?", (user_id,))
        energy = cursor.fetchall()[0][0]
        if energy == 0:
            cursor2.execute("UPDATE programs SET status = ? WHERE user_id = ?", ('no', user_id))
            conn2.commit()
            cursor.execute("UPDATE users SET status = ? WHERE user_id = ?", ('бездельничает', user_id))
            conn.commit()
            await bot.send_message(user_id, "<b>😓Ваш персонаж устал и не может больше работать</b>", parse_mode='html')
        else:
            cursor2.execute("UPDATE programs SET time = time - 1 WHERE user_id = ?", (user_id,))
            conn2.commit()
            cursor.execute("UPDATE users SET energy = energy - 1, rep = rep + 20 WHERE user_id = ?", (user_id,))
            conn.commit()
            cursor2.execute("SELECT time, status FROM programs WHERE user_id = ?", (user_id,))
            if cursor2:
                flag, status = cursor2.fetchone()
            if flag <= 0 and status != 'ready':
                cursor2.execute("UPDATE programs SET status = ? WHERE user_id = ?", ('ready', user_id))
                conn2.commit()
                cursor.execute("UPDATE users SET status = ? WHERE user_id = ?", ('бездельничает', user_id))
                conn.commit()
                keyboard = InlineKeyboardMarkup(row_width=1)
                keyboard.add(
                    InlineKeyboardButton("👉Перейти к задаче", callback_data=f"program_status:{user_id}")
                )     
                await bot.send_message(user_id, "<b>👍Задача польностью завершена</b>", reply_markup=keyboard, parse_mode='html')

async def game_pay():
    for user_id in users_games_set:
        if os.path.exists(f'{user_id}.db'):
            conn6 = sqlite3.connect(f'{user_id}.db')
            cursor6 = conn6.cursor()
            if cursor6.execute("SELECT i FROM games").fetchone() == None:
                conn6.close()
                os.remove(f'{user_id}.db')
                users_games_set.discard(user_id)
            else:
                for game in cursor6.execute("SELECT i, time, count, price, donate, name FROM games").fetchall():
                    idd, time, count, price, donate, name = game                           
                    cursor6.execute("UPDATE games SET time = time - 1 WHERE i == ?", (idd,))
                    conn6.commit()                                            
                    if time - 1 == 0:
                        itog_price = random.randint(int(price * 0.9), int(price * 1.1))   
                        itog_donate = random.randint(0, 4) + random.randint(0, 9) / 10
                        cursor = conn.cursor()                        
                        cursor.execute("UPDATE users SET ruble = ruble + ?, toncoin = toncoin + ? WHERE user_id == ?", (itog_price, itog_donate, user_id))
                        conn.commit()   
                        cursor6.execute("UPDATE games SET summ = summ + ?, donate = donate + ? WHERE i == ?", (itog_price, itog_donate, idd))
                        conn6.commit()                         
                        keyboard = InlineKeyboardMarkup(row_width=1)
                        keyboard.add(
                            InlineKeyboardButton("👍Круто!", callback_data=f"profile:{user_id}")
                        )                     
                        await bot.send_message(user_id, f'<b>💸Игра: "{name}" принесла создателю {itog_price} ₽ и {itog_donate} TON в качестве добровольной поддержки</b>', reply_markup=keyboard, parse_mode='html')                       
                        if count != 3:                                            
                            cursor6.execute("UPDATE games SET time = 36, count = count + 1 WHERE i == ?", (idd,))
                            conn6.commit()                       
                        else:
                            cursor6.execute("DELETE FROM games WHERE i = ?", (idd,))
                            conn6.commit()  
                            await bot.send_message(user_id, f'<b>❗️Игра снята с платформы и больше не принесёт вам денег</b>', parse_mode='html') 

async def hack_work_gen():
    cursor.execute("SELECT user_id FROM users WHERE status = ?", ('бездельничает',))
    hack_work_users = cursor.fetchall()
    for user_id in hack_work_users:
        user_id = user_id[0] 
        if int(random.choices([1, 0], weights=[1, 9], k=1)[0]) == 1 and cursor2.execute("SELECT user_id FROM programs WHERE user_id = ?", (user_id,)).fetchone() == None:
            time = int(random.choices([4, 5, 6, 7, 8], weights=[1, 2, 3, 4, 5], k=1)[0])
            price = round(time * float(random.choices([1.5, 1.8, 1.7, 1.6, 1.5], weights=[1, 2, 3, 4, 5], k=1)[0]), 1)
            rep = int(price * 50)
            name = random.choices(anon_name)[0]
            end = random.choices(anon_end)[0]
            work = random.choices(hack_work_list)[0]
            hack_work_dict[user_id] = work
            if end == 'random':
                end = ''
                for i in range(random.randint(3, 7)):
                    end += str(random.randint(0, 10))
            name += end
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                InlineKeyboardButton("✅Принять", callback_data=f"hack_work_g:{user_id}:{time}:{price}:{rep}"),
                InlineKeyboardButton("❌Отказаться", callback_data=f"hack_work_b:{user_id}")
            )
            text = f'''<b>📟Вам пришло задание от {name}:</b>
            
<b>Задача: {work}</b>
<b>Время выполнения: {time} ч.</b>
<b>Доход: {price} TON</b>
<b>Репутация: -{rep}</b>'''
            await bot.send_message(user_id, text, reply_markup=keyboard, parse_mode='html')

async def scheduler():
    aioschedule.every(30).minutes.do(decrease_hunger)
    aioschedule.every(5).minutes.do(sleep)
    aioschedule.every(15).minutes.do(work)
    aioschedule.every(2).hours.do(game_pay)
    aioschedule.every(1).hours.do(hack_work_gen)
    
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(10)

async def on_startup(dp):    
    asyncio.create_task(scheduler())       
    
@dp.message_handler(commands=['stop'])
async def stop_global(message: types.Message):
    user_id = message.from_user.id
    if admin_id == user_id:
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("✅Да", callback_data=f"stop_global_a:{user_id}"),
            InlineKeyboardButton("❌Нет", callback_data=f"stop_global_b:{user_id}")                  
                ) 
        await bot.send_message(user_id, "Уверен, что хочешь отключить бота?", reply_markup=keyboard)
        
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'stop_global_a')
async def stop_global_a(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    await bot.send_message(user_id, "Программа отключена") 
    await bot.delete_message(user_id, callback_query.message.message_id)    
    exit()
        
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'stop_global_b')
async def stop_global_b(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    await bot.send_message(user_id, "Фух, спасибо, что ты меня не отключил") 
    await bot.delete_message(user_id, callback_query.message.message_id)    
        
@dp.message_handler(commands=['admin'])
async def admin_m(message: types.Message):
    await admin(message)
    
@dp.message_handler(commands=["ref"])
async def get_ref(message: types.Message):
    link = await get_start_link(str(message.from_user.id), encode=True)
    await message.answer(f"<b>🔥Ваша реферальная ссылка ссылка:\n\n{link}\n\n📌Вы получите: 10 TON за переход\n📌Реферал получит: 20 TON</b>", parse_mode='html')
    
@dp.message_handler(commands=["fact"])
async def get_fact(message: types.Message):
    user_id = message.from_user.id    
    text = requests.get('https://catfact.ninja/fact/').json()['fact']
    transleted = GoogleTranslator(source='en', target='ru').translate(text) 
    keyboard = InlineKeyboardMarkup()    
    keyboard.add(
        InlineKeyboardButton("🖼Перейти в профиль", callback_data=f"profile:{user_id}")
    )    
    await message.answer(f'<b>👉{transleted}\n\n<a href="https://t.me/cat_in_code_bot">#КОТ_В_КОДЕ</a></b>', reply_markup=keyboard, disable_web_page_preview = True, parse_mode='html')
    
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    try:
        args = message.get_args()
        reference = decode_payload(args)
    except:
        reference = ''
    cursor.execute("SELECT status FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("🖼Перейти в профиль", callback_data=f"profile:{user_id}")
        )
    if not result or result[0] == 'выбыл':
        telegram_name = message.from_user.first_name
        try:
            telegram_name += ' ' + message.from_user.last_name
        except:
            pass
        try:
            cursor2.execute("DELETE FROM programs WHERE user_id = ?", (user_id,))
            conn2.commit()
        except:
            pass
        if os.path.exists(f'{user_id}.db'):
            os.remove(f'{user_id}.db')        
        if user_id in users_games_set:
            users_games_set.remove(user_id)
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        cursor.execute("INSERT OR IGNORE INTO users (user_id, telegram_name, energy, health, hunger, status, rep, ruble, dollar, toncoin, exchange, skill, computer, flag) VALUES (?, ?, 100, 100, 100, 'бездельничает', 0, 10000, 0, 0, '', 0, 'digma', 'None')", (user_id, telegram_name))
        conn.commit()
        beta_test_users_set.add(user_id)
        beta_test_users_file = open("Resources/beta.txt", "a")
        beta_test_users_file.write(str(user_id))
        beta_test_users_file.write('\n')        
        beta_test_users_file.close()        
        await message.answer("<b>👋Привет! Ты в игре. Теперь ты зарегистрирован. Не забудь вступить в канал: @cat_in_code_beta</b>\n\n<b><i>⚙️Ты можешь воспользоваться командой: /info, чтобы узнать больше информации о боте</i></b>", reply_markup=keyboard, parse_mode='html')
        if reference != '' and int(reference) != user_id:
            await message.answer("<b><i>🔥Ты перешёл по реферальной ссылке. Твоё вознаграждение - 20 TON</i></b>", parse_mode='html')
            cursor.execute("UPDATE users SET toncoin = toncoin + 20 WHERE user_id = ?", (user_id,))
            cursor.execute("UPDATE OR IGNORE users SET toncoin = toncoin + 10 WHERE user_id = ?", (int(reference),))
            conn.commit()                
            try:
                await bot.send_message(int(reference), "<b><i>🔥Реферал перешёл по твоей ссылке. Твоё вознаграждение - 10 TON</i></b>", parse_mode='html')              
            except:
                pass
    else:
        await message.answer("<b>✅Ты уже зарегистрирован</b>\n\n<b><i>⚙️Ты можешь воспользоваться командой: /info, чтобы узнать больше информации о боте</i></b>", reply_markup=keyboard, parse_mode='html')

@dp.message_handler(commands=['info'])
async def info(message: types.Message):
    user_id = message.from_user.id
    keyboard = InlineKeyboardMarkup(row_width=1)    
    keyboard.add(    
    InlineKeyboardButton(text="🎓WiKi", web_app=WebAppInfo(url='https://telegra.ph/KOT-V-KODE---WiKi-02-18')),
    InlineKeyboardButton(text="🏆Поддержать проект", web_app=WebAppInfo(url='https://www.donationalerts.com/r/i_maxxl')),
    InlineKeyboardButton("🖼Перейти в профиль", callback_data=f"profile:{user_id}")
    )    
    await bot.send_message(user_id, '<b>#КОТ_В_КОДЕ - это уникальный Телеграм-бот, в котором пользователь погрузится в виртуальный мир жизни кота-программиста\n\n🧶Получить реферальную ссылку: /ref\n\n😺Прочитать случайный факт о котах: /fact\n\n📌Узнать свой рейтинг среди игроков: /leaderboard\n\n👉Более подробно изучить все функции бота можно <a href="https://telegra.ph/KOT-V-KODE---WiKi-02-18">в статье</a></b>', reply_markup=keyboard, parse_mode='html')

@dp.message_handler(commands=['leaderboard'])
async def leaderboard(message: types.Message):
    user_id = message.from_user.id    
    all_users = cursor.execute("SELECT user_id, rep, telegram_name FROM users WHERE status != 'выбыл' ORDER BY rep DESC LIMIT 10").fetchall()
    this_user = conn.execute("SELECT user_id, rep, telegram_name, RANK() OVER (ORDER BY rep DESC) AS rank FROM users WHERE status != 'выбыл'").fetchall()
    for i in this_user:
        if i[0] == user_id:
            this_user = i
            break
    c = 1
    leaderboard_text = "<b>⚡️Таблица лидеров:\n\n<i>👉Репутация | Имя\n</i></b>"
    for user in all_users:
        if user[0] in beta_test_users_set:
            leaderboard_text += f"{c}. {user[1]} | {user[2]} - <b>(β)</b>\n"
        else:
            leaderboard_text += f"{c}. {user[1]} | {user[2]}\n"            
        c += 1
    leaderboard_text += "<b><i>...\n</i></b>"
    if this_user[0] in beta_test_users_set:    
        leaderboard_text += f"<b>{this_user[3]}. {this_user[1]} | {this_user[2]} - <b>(β)</b> - ВЫ</b>\n"
    else:
        leaderboard_text += f"<b>{this_user[3]}. {this_user[1]} | {this_user[2]} - ВЫ</b>\n"        
    await bot.send_message(user_id, leaderboard_text, parse_mode='html')    
        
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'shop')
async def shop_m(callback_query: types.CallbackQuery):
    await shop(callback_query)

@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'hack_work_g')
async def hack_work_g(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return
    if await check_work(user_id, callback_query):
        return 
    time = int(callback_query.data.split(':')[2]) * 4
    price = float(callback_query.data.split(':')[3])
    rep = int(callback_query.data.split(':')[4])
    try:
        work = hack_work_dict[user_id]
        del hack_work_dict[user_id]
    
        cursor.execute("UPDATE users SET rep = rep - ? WHERE user_id = ?", (rep, user_id,))
        conn.commit()       
    
        cursor2.execute("INSERT OR IGNORE INTO programs (user_id, name, description, time, price, skill, status, type, currency) VALUES (?, ?, ?, ?, ?, ?, 'no', 'hack', 'ton')", (    user_id, work, work, time, price, 0))
        conn2.commit()   
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton("✅Перейти", callback_data=f"program_status:{user_id}"))         
        await bot.send_message(user_id, f"<b>👌Вы приняли задачу и можете приступить к выполнению:</b>", reply_markup=keyboard, parse_mode='html')
        await bot.delete_message(user_id, callback_query.message.message_id)
    except:
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton("🖼Перейти в профиль", callback_data=f"profile:{user_id}"))
        await bot.send_message(user_id, f"<b>❌Эта задача уже неауктальна</b>", reply_markup=keyboard, parse_mode='html')
        await bot.delete_message(user_id, callback_query.message.message_id)        
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'hack_work_b')
async def hack_work_b(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return
    try:
        del hack_work_dict[user_id]
    except:
        pass
    await bot.send_message(user_id, f"<b>👌Задача отменена</b>", parse_mode='html')    
    await bot.delete_message(user_id, callback_query.message.message_id)    
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'tasks')
async def possible_tasks(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return    
    cursor2.execute("SELECT status FROM programs WHERE user_id = ?", (user_id,))
    result = cursor2.fetchone()
    if result:
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton("👀Посмотреть", callback_data=f"program_status:{user_id}"))
        keyboard.add(InlineKeyboardButton("↩️Вернуться в профиль", callback_data=f"profile:{user_id}"))        
        await bot.send_message(user_id, "<b>❗️У вас уже есть активные задания</b>", reply_markup=keyboard, parse_mode='html')
        await bot.delete_message(user_id, callback_query.message.message_id)
        
    else:
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton("💽Написать скрипт", callback_data=f"makescript:{user_id}"))        
        keyboard.add(InlineKeyboardButton("💾Написать свою программу", callback_data=f"makeprogram:{user_id}"))
        keyboard.add(InlineKeyboardButton("🕹Написать свою игру", callback_data=f"makegame:{user_id}"))    
        keyboard.add(InlineKeyboardButton("❌Отмена", callback_data=f"profile:{user_id}"))

        await bot.send_message(user_id, "<b>👉Выберите тип задания:</b>", reply_markup=keyboard, parse_mode='html')
        await bot.delete_message(user_id, callback_query.message.message_id)
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'makescript')
async def makescript_choice(callback_query: types.CallbackQuery):
    global message_text
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return
    if await check_work(user_id, callback_query):
        return 
    message_text = ''
    keyboard = InlineKeyboardMarkup(row_width=3) 
    data = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()['Valute']['USD']['Value']
    async def create_script_task(i):
        global message_text
        time = random.randint(4, 12)
        k = random.randint(150, 200)
        company = random.choice(company_list)
        job = random.choice(jobs_list)
        price = int(time * k / 4)
        if company_dict[company] == '$':
            price = int(price * (1 / data) + 0.99)
        message_text = message_text + f'<b>{i}. Компания: {company}</b> ⏰: {round(time / 4, 2)} ч. 💳: {price}{company_dict[company]}\nЗадача: {job}\n'
        return InlineKeyboardButton(str(i), callback_data=f"a_script:{user_id}:{company_list.index(company)}:{jobs_list.index(job)}:{time}:{price}:{company_dict[company]}")
        
    for i in range(1, 7, 3):
        keyboard.add(await create_script_task(i), await create_script_task(i + 1), await create_script_task(i + 2))
           
    keyboard.add(InlineKeyboardButton("❌Отмена", callback_data=f"profile:{user_id}"))
    message_text += '\n'
    message_text += '<b>Выберите задачу или отмените её:</b>'
    await bot.send_message(user_id, message_text, reply_markup=keyboard, parse_mode='html')
    await bot.delete_message(user_id, callback_query.message.message_id)    
   
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'a_script')
async def a_script(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return 
    if await check_work(user_id, callback_query):
        return     
    user_id, name, description, time, price, currency = callback_query.data.split(':')[1:]
    user_id, name, description, time, price = int(user_id), company_list[int(name)].strip(), jobs_list[int(description)].strip(), int(time), int(price) 
    name = f'{name} - {description}'
    if currency == '₽':
        currency = 'rub'
    else:
        currency = 'usd'
    cursor2.execute("INSERT OR IGNORE INTO programs (user_id, name, description, time, price, skill, status, type, currency) VALUES (?, ?, ?, ?, ?, ?, 'no', 'script', ?)", (user_id, name, description, int(time), price, 0, currency))
    conn2.commit()   
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("✅Перейти", callback_data=f"program_status:{user_id}"))         
    await bot.send_message(user_id, f"<b>👌Вы приняли задачу и можете приступить к выполнению:</b>", reply_markup=keyboard, parse_mode='html')
    await bot.delete_message(user_id, callback_query.message.message_id)
   
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'makegame')
async def makegame_start(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return
    if await check_work(user_id, callback_query):
        return 
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("❌Отмена", callback_data=f"profile:{user_id}"))
    await bot.send_message(user_id, '<b>👉Введите название вашей игры:\n\n<i>НЕ используйте символ "." (точка)</i></b>', reply_markup=keyboard, parse_mode='html')
    cursor.execute("UPDATE users SET flag = ? WHERE user_id = ?", ('game_name', user_id))
    conn.commit()   
    await bot.delete_message(user_id, callback_query.message.message_id)  
    
@dp.message_handler(lambda message: message.text and cursor.execute("SELECT flag FROM users WHERE user_id = ?", (message.chat.id,)).fetchone()[0] == 'game_name' and '.' not in message.text)
async def makegame_name(message: types.Message):
    user_id = message.chat.id
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("❌Отмена", callback_data=f"profile:{user_id}"))
    await bot.send_message(user_id, f"<b>✅Название сохранено:\n\nВведите описание вашей игры:</b>", reply_markup=keyboard, parse_mode='html')
    cursor.execute("UPDATE users SET flag = ? WHERE user_id = ?", (f'game_name_description.{message.text}', user_id))
    conn.commit()      
    
@dp.message_handler(lambda message: message.text and cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (message.chat.id,)).fetchone() and cursor.execute("SELECT flag FROM users WHERE user_id = ?", (message.chat.id,)).fetchone()[0].split('.')[0] == 'game_name_description')
async def makegame_description(message: types.Message):
    global programsdict
    user_id = message.chat.id
    flag = cursor.execute("SELECT flag FROM users WHERE user_id = ?", (message.chat.id,)).fetchone()[0] + '.' + message.text
    cursor.execute("UPDATE users SET flag = ? WHERE user_id = ?", (flag, user_id))
    conn.commit()
    
    hourname = ''  
    cursor.execute("SELECT skill, flag FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    skill, name, description = result[0], result[1].split('.')[1], result[1].split('.')[2]
    time = random.choices(random.choices([[5,6,7,8], [9,10,11,12], [13,14,15,16], [17,18,19,20], [21,22,23,24]], weights=[15, 20, 30, 20, 15], k=1)[0])[0]      
    price = int(int(time) * (150 - int(random.choices([10, 20, 30, 40, 50, 60, 70], weights=[24, 20, 16, 13, 11, 9, 7], k=1)[0]) + random.randint(1, 9)))
    cursor.execute("SELECT computer FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()[0]   
    time = (time / ((skill / 1000) + 1)) / technic_products[result][2]['speed']
    if int(time) in [2, 3, 4, 22, 23, 24]:
        hourname = 'часа'
    elif int(time) in [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]:
        hourname = 'часов'
    elif int(time) in [1, 21]:
        hourname = 'час'
    button_text = f"makegame_accept:{user_id}"
    programsdict[user_id] = f"{user_id}:{name}:{description}:{time}:{price}:{skill}"
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("✅Принять задачу", callback_data=button_text)) 
    keyboard.add(InlineKeyboardButton("❌Отмена", callback_data=f"profile:{user_id}"))
    await bot.send_message(user_id, f'<b>✅Описание сохранено\n\nИнформация по игре "{name}":\n\nПримерное время разработки:</b> {round(time, 1)} {hourname}\n<b>Примерная цена продажи:</b> {price}x4 ₽', reply_markup=keyboard, parse_mode='html')
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'makegame_accept')
async def makegame_accept(callback_query: types.CallbackQuery):
    global programsdict    
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return
    if await check_work(user_id, callback_query):
        return     
    user_id, name, description, time, price, skill = programsdict[user_id].split(':')
    user_id, time, price, skill = int(user_id), float(time) * 4, int(price), int(skill)    
    del programsdict[user_id]
    cursor2.execute("INSERT OR IGNORE INTO programs (user_id, name, description, time, price, skill, status, type, currency) VALUES (?, ?, ?, ?, ?, ?, 'no', 'game', 'rub')", (user_id, name, description, int(time), price, skill))
    conn2.commit()
    cursor.execute("UPDATE users SET flag = 'process' WHERE user_id = ?", (user_id,))
    conn.commit()    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("✅Перейти", callback_data=f"program_status:{user_id}"))         
    await bot.send_message(user_id, f"<b>👌Вы приняли задачу и можете приступить к выполнению:</b>", reply_markup=keyboard, parse_mode='html')
    await bot.delete_message(user_id, callback_query.message.message_id)
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'makeprogram')
async def makeprogram_start(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return
    if await check_work(user_id, callback_query):
        return     
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("❌Отмена", callback_data=f"profile:{user_id}"))
    await bot.send_message(user_id, '<b>👉Введите название вашей программы:\n\n<i>НЕ используйте символ "." (точка)</i></b>', reply_markup=keyboard, parse_mode='html')
    cursor.execute("UPDATE users SET flag = ? WHERE user_id = ?", ('program_name', user_id))
    conn.commit()   
    await bot.delete_message(user_id, callback_query.message.message_id)    
    
@dp.message_handler(lambda message: message.text and cursor.execute("SELECT flag FROM users WHERE user_id = ?", (message.chat.id,)).fetchone()[0] == 'program_name' and '.' not in message.text)
async def makeprogram_name(message: types.Message):
    user_id = message.chat.id
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("❌Отмена", callback_data=f"profile:{user_id}"))
    await bot.send_message(user_id, f"<b>✅Название сохранено:\n\nВведите описание вашей программы:</b>", reply_markup=keyboard, parse_mode='html')
    cursor.execute("UPDATE users SET flag = ? WHERE user_id = ?", (f'program_name_description.{message.text}', user_id))
    conn.commit()      
    
@dp.message_handler(lambda message: message.text and cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (message.chat.id,)).fetchone() and cursor.execute("SELECT flag FROM users WHERE user_id = ?", (message.chat.id,)).fetchone()[0].split('.')[0] == 'program_name_description')
async def makeprogram_description(message: types.Message):
    global programsdict
    user_id = message.chat.id
    flag = cursor.execute("SELECT flag FROM users WHERE user_id = ?", (message.chat.id,)).fetchone()[0] + '.' + message.text
    cursor.execute("UPDATE users SET flag = ? WHERE user_id = ?", (flag, user_id))
    conn.commit()
    
    hourname = ''
    cursor.execute("SELECT skill, flag FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    skill, name, description = result[0], result[1].split('.')[1], result[1].split('.')[2]
    time = random.choices(random.choices([[5,6,7,8], [9,10,11,12], [13,14,15,16], [17,18,19,20], [21,22,23,24]], weights=[15, 20, 30, 20, 15], k=1)[0])[0]      
    price = int(2 * int(time) * (150 - int(random.choices([10, 20, 30, 40, 50, 60, 70], weights=[24, 20, 16, 13, 11, 9, 7], k=1)[0]) + random.randint(1, 9) / 2))
    cursor.execute("SELECT computer FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()[0]   
    time = (time / ((skill / 1000) + 1)) / technic_products[result][2]['speed']
    if int(time) in [2, 3, 4, 22, 23, 24]:
        hourname = 'часа'
    elif int(time) in [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]:
        hourname = 'часов'
    elif int(time) in [1, 21]:
        hourname = 'час'   
    button_text = f"makeprogram_accept:{user_id}"
    programsdict[user_id] = f"{user_id}:{name}:{description}:{time}:{price}:{skill}"
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("✅Принять задачу", callback_data=button_text)) 
    keyboard.add(InlineKeyboardButton("❌Отмена", callback_data=f"profile:{user_id}"))
    await bot.send_message(user_id, f'<b>✅Описание сохранено\n\nИнформация по программе "{name}":\n\nПримерное время разработки:</b> {round(time, 1)} {hourname}\n<b>Примерная цена продажи:</b> {price} ₽', reply_markup=keyboard, parse_mode='html')

@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'makeprogram_accept')
async def makeprogram_accept(callback_query: types.CallbackQuery):
    global programsdict    
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return
    if await check_work(user_id, callback_query):
        return 
    user_id, name, description, time, price, skill = programsdict[user_id].split(':')
    user_id, time, price, skill = int(user_id), float(time) * 4, int(price), int(skill)    
    del programsdict[user_id]
    cursor2.execute("INSERT OR IGNORE INTO programs (user_id, name, description, time, price, skill, status, type, currency) VALUES (?, ?, ?, ?, ?, ?, 'no', 'programm', 'rub')", (user_id, name, description, int(time), price, skill))
    conn2.commit()
    cursor.execute("UPDATE users SET flag = 'process' WHERE user_id = ?", (user_id,))
    conn.commit()    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("✅Перейти", callback_data=f"program_status:{user_id}"))         
    await bot.send_message(user_id, f"<b>👌Вы приняли задачу и можете приступить к выполнению:</b>", reply_markup=keyboard, parse_mode='html')
    await bot.delete_message(user_id, callback_query.message.message_id)
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'program_status')
async def program_status(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return    
    result = cursor2.execute("SELECT status, type FROM programs WHERE user_id = ?", (user_id,)).fetchone()
    if result:    
        status_work, typee = result
        if status_work == 'no':
            status_work = 'Не активна'
            button_status = '👉Начать работу'
        elif status_work == 'yes':
            status_work = 'В работе'
            button_status = '😴Снять задачу'
        else:
            status_work = 'Выполнена'
            if typee == 'script':
                button_status = '🤝Отправить работодателю'
            elif typee == 'programm':
                button_status = '🧮Выставить программу на аукцион'
            elif typee == 'game':
                button_status = '🎮Опубликовать игру'
            else:
                button_status = '🗄Сдать задачу'
                
        keyboard = InlineKeyboardMarkup(row_width=1)
        if button_status in ['👉Начать работу', '😴Снять задачу']:
            keyboard.add(InlineKeyboardButton(button_status, callback_data=f"swap_status:{user_id}"))
        elif button_status == '🤝Отправить работодателю':
            keyboard.add(InlineKeyboardButton(button_status, callback_data=f"submit_job:{user_id}"))
        elif button_status == '🎮Опубликовать игру':
            keyboard.add(InlineKeyboardButton(button_status, callback_data=f"publish:{user_id}"))
        elif button_status == '🗄Сдать задачу':
            keyboard.add(InlineKeyboardButton(button_status, callback_data=f"hack_done:{user_id}"))        
        else:
            keyboard.add(InlineKeyboardButton(button_status, callback_data=f"auction:{user_id}"))            
        keyboard.add(InlineKeyboardButton("🗑Удалить задачу", callback_data=f"program_delete_1:{user_id}")) 
        keyboard.add(InlineKeyboardButton("🔄Обновить", callback_data=f"program_status:{user_id}"))          
        keyboard.add(InlineKeyboardButton("🖼Перейти в профиль", callback_data=f"profile:{user_id}"))
        await bot.delete_message(user_id, callback_query.message.message_id)
        
        program_name = cursor2.execute("SELECT name FROM programs WHERE user_id = ?", (user_id,)).fetchone()[0]
        program_time = round(cursor2.execute("SELECT time FROM programs WHERE user_id = ?", (user_id,)).fetchone()[0] / 4, 1)
        hourname = ''
        if int(program_time) in [2, 3, 4, 22, 23, 24]:
            hourname = 'часа'
        elif int(program_time) in [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]:
            hourname = 'часов'
        elif int(program_time) in [1, 21]:
            hourname = 'час'             
        await bot.send_message(user_id, f'<b>📂Активная задача: "{program_name}"\n\n👌Статус задачи:</b> {status_work}\n<b>⏰Примерное время выполнения:</b> {program_time} {hourname}', reply_markup=keyboard, parse_mode='html')    
    else:
        keyboard = InlineKeyboardMarkup(row_width=1)        
        keyboard.add(InlineKeyboardButton("👨‍💻Доступные задачи", callback_data=f"tasks:{user_id}"))
        keyboard.add(InlineKeyboardButton("🖼Перейти в профиль", callback_data=f"profile:{user_id}"))
        await bot.delete_message(user_id, callback_query.message.message_id)        
        await bot.send_message(user_id, f"<b>🤓Задач нет, вы можете начать новую:</b>", reply_markup=keyboard, parse_mode='html') 
        
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'swap_status')
async def program_swap(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return    
    try:
        status_work = cursor2.execute("SELECT status FROM programs WHERE user_id = ?", (user_id,)).fetchone()[0]
        if status_work == 'no':
            cursor2.execute("UPDATE programs SET status = ? WHERE user_id = ?", ('yes', user_id))
            project = cursor2.execute("SELECT name FROM programs WHERE user_id = ?", (user_id,)).fetchone()[0]
            cursor.execute("UPDATE users SET status = ? WHERE user_id = ?", (f'Работает над проектом "{project}"', user_id))        
        else:
            cursor2.execute("UPDATE programs SET status = ? WHERE user_id = ?", ('no', user_id))
            cursor.execute("UPDATE users SET status = ? WHERE user_id = ?", ('бездельничает', user_id))   
        conn2.commit()
        conn.commit()        
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton("↩️Вернуться", callback_data=f"program_status:{user_id}"))
        await bot.delete_message(user_id, callback_query.message.message_id)        
        await bot.send_message(user_id, f"<b>👌Статус изменён</b>", reply_markup=keyboard, parse_mode='html')
    except:
        await bot.delete_message(user_id, callback_query.message.message_id)        
        await bot.send_message(user_id, f"<b>❗️Задача была удалена</b>", parse_mode='html')        
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'program_delete_1')
async def program_delete_1(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅Да", callback_data=f"program_delete:{user_id}"),
        InlineKeyboardButton("❌Нет", callback_data=f"program_status:{user_id}")                  
            ) 
    await bot.delete_message(user_id, callback_query.message.message_id)            
    await bot.send_message(user_id, "<b>Ты точно что хочешь удалить задачу?</b>", reply_markup=keyboard, parse_mode='html')
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'program_delete')
async def program_delete(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return    
    try:
        cursor2.execute("DELETE FROM programs WHERE user_id = ?", (user_id,))   
        cursor.execute("UPDATE users SET status = ?, rep = rep - 100 WHERE user_id = ?", ('бездельничает', user_id))
        await bot.send_message(user_id, f"<b>👌Ваша задача удалена</b>", parse_mode='html')
        await bot.delete_message(user_id, callback_query.message.message_id)        
        await cmd_profile(types.CallbackQuery(data=f"profile:{user_id}"))
        conn2.commit()
        conn.commit()        
    except:
        await bot.delete_message(user_id, callback_query.message.message_id)        
        await bot.send_message(user_id, f"<b>❗️Задача была удалена</b>", parse_mode='html')      
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'submit_job')
async def submit_job(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])  
    if await check_life(user_id, callback_query):
        return    
    if cursor2.execute("SELECT type FROM programs WHERE user_id = ?", (user_id,)).fetchone() != ('script',):
        await bot.send_message(user_id, f"<b>❌Действие недоступно</b>", parse_mode='html')     
        return    
    cursor2.execute("SELECT price, currency FROM programs WHERE user_id = ?", (user_id,))   
    price, currency = cursor2.fetchone()
    price = int(price)
    cursor2.execute("DELETE FROM programs WHERE user_id = ?", (user_id,))
    conn2.commit()   
    keyboard = InlineKeyboardMarkup(row_width=1)           
    keyboard.add(InlineKeyboardButton("↩️Вернуться в профиль", callback_data=f"profile:{user_id}"))     
    if currency == 'rub':
        cursor.execute("UPDATE users SET ruble = ruble + ? WHERE user_id = ?", (price, user_id))       
        await bot.send_message(user_id, f"<b>Задача отправлена, на баланс начислено {price}₽</b>", reply_markup=keyboard, parse_mode='html')
    else:
        cursor.execute("UPDATE users SET dollar = dollar + ? WHERE user_id = ?", (price, user_id))       
        await bot.send_message(user_id, f"<b>Задача отправлена, на баланс начислено {price}$</b>", reply_markup=keyboard, parse_mode='html')        
    conn.commit()    
    await bot.delete_message(user_id, callback_query.message.message_id)        
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'auction')
async def auction(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])  
    if await check_life(user_id, callback_query):
        return  
    if cursor2.execute("SELECT type FROM programs WHERE user_id = ?", (user_id,)).fetchone() != ('programm',):
        await bot.send_message(user_id, f"<b>❌Действие недоступно</b>", parse_mode='html')     
        return
    try:
        keyboard = InlineKeyboardMarkup(row_width=1)       
        keyboard.add(InlineKeyboardButton("🇷🇺Выставить на СНГ биржу", callback_data=f"program_market:{user_id}:rub"))    
        keyboard.add(InlineKeyboardButton("🗺Выставить на зарубежную биржу", callback_data=f"program_market:{user_id}:usd"))
        keyboard.add(InlineKeyboardButton("🖼Перейти в профиль", callback_data=f"profile:{user_id}"))    
        await bot.delete_message(user_id, callback_query.message.message_id)            
        await bot.send_message(user_id, f"<b>🛎Выберите действие:</b>", reply_markup=keyboard, parse_mode='html')    
    except:
        await bot.delete_message(user_id, callback_query.message.message_id)        
        await bot.send_message(user_id, f"<b>❗️Задача была удалена</b>", reply_markup=keyboard, parse_mode='html')  
        
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'program_market')
async def sng_market(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return   
    if cursor2.execute("SELECT type FROM programs WHERE user_id = ?", (user_id,)).fetchone() != ('programm',):
        await bot.send_message(user_id, f"<b>❌Действие недоступно</b>", parse_mode='html')     
        return    
    money_flag = callback_query.data.split(':')[2]
    if money_flag == 'rub':
        money_name = '₽'
    else:
        money_name = '$'    
    await bot.delete_message(user_id, callback_query.message.message_id)            
    cursor2.execute("SELECT price FROM programs WHERE user_id = ?", (user_id,))   
    price = cursor2.fetchall()[0][0]
    cursor2.execute("DELETE FROM programs WHERE user_id = ?", (user_id,))
    conn2.commit()      
    if money_flag == 'rub':
        step = price // 20
        itog_price = random.randint(int(price * 0.9), int(price * 1.1))
    else:
        data = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
        price = price * round(1 / data['Valute']['USD']['Value'], 5)
        step = price // 20
        itog_price = random.randint(int(price * 0.75), int(price * 1.25))        
    
    if money_flag == 'rub':
        cursor.execute("UPDATE users SET ruble = ruble + ? WHERE user_id = ?", (itog_price, user_id))
    else:
        cursor.execute("UPDATE users SET dollar = dollar + ? WHERE user_id = ?", (itog_price, user_id))        
    conn.commit()        
    
    msg = await bot.send_message(user_id, f"<b>Торги начинаются...</b>", parse_mode='html')
    count = random.randint(4, 6)
    if step == 0:
        step = 1
    for i in range(count - 1, -1, -1):
        await asyncio.sleep(1)        
        await msg.edit_text(f"🤚 {itog_price - step * i} {money_name}")
    msg = await bot.send_message(user_id, "3...")
    await asyncio.sleep(1)
    await msg.edit_text("3...2...")
    await asyncio.sleep(1)            
    await msg.edit_text("3...2...1...")
    await asyncio.sleep(1)
    await msg.edit_text(f"Продано за: {itog_price} {money_name}")
    
    keyboard = InlineKeyboardMarkup(row_width=1)           
    keyboard.add(InlineKeyboardButton("↩️Вернуться в профиль", callback_data=f"profile:{user_id}"))  
    await bot.send_message(user_id, f"<b>👌{itog_price} {money_name} начисленно на баланс</b>", reply_markup=keyboard, parse_mode='html')
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'publish')
async def publish(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return   
    if cursor2.execute("SELECT type FROM programs WHERE user_id = ?", (user_id,)).fetchone() != ('game',):
        await bot.send_message(user_id, f"<b>❌Действие недоступно</b>", parse_mode='html')     
        return    
    conn4 = sqlite3.connect(f'{user_id}.db')
    cursor4 = conn4.cursor()
    cursor4.execute('''
        CREATE TABLE IF NOT EXISTS games (
            i INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            time INTEGER,
            price INTEGER,
            count INTEGER,
            summ INTEGER,
            donate INTEGER
        )
    ''')
    conn4.commit()          
    name, time, price = cursor2.execute("SELECT name, time, price FROM programs WHERE user_id = ?", (user_id,)).fetchone()
    time, price = int(time), int(price)
    cursor4.execute("INSERT INTO games (name, time, price, count, summ, donate) VALUES (?, 36, ?, 0, 0, 0)", (name, price))
    conn4.commit()      
    
    if user_id not in users_games_set:
        users_games_set.add(user_id)
        users_games_file = open("Resources/games.txt", "a")
        users_games_file.write(str(user_id))
        users_games_file.write('\n')        
        users_games_file.close()
    
    cursor2.execute("DELETE FROM programs WHERE user_id = ?", (user_id,))
    conn2.commit()  
    
    keyboard = InlineKeyboardMarkup(row_width=1)           
    keyboard.add(InlineKeyboardButton("↩️Вернуться в профиль", callback_data=f"profile:{user_id}"))        
    await bot.delete_message(user_id, callback_query.message.message_id)        
    await bot.send_message(user_id, f'<b>👌Игра: "{name}" опубликована</b>', reply_markup=keyboard, parse_mode='html')
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'my_games')
async def my_games(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return    
    if os.path.exists(f'{user_id}.db'):
        conn5 = sqlite3.connect(f'{user_id}.db')
        cursor5 = conn5.cursor()
        keyboard = InlineKeyboardMarkup(row_width=1)           
        keyboard.add(InlineKeyboardButton("↩️Вернуться в профиль", callback_data=f"profile:{user_id}"))  
        text = ''
        j = 1
        for i in cursor5.execute("SELECT name, summ, donate FROM games").fetchall():
            text += f'{j}. 🕹Игра: "{i[0]}" 💰Заработала: {i[1]} ₽ и {i[2]} TON' + "\n"
            j += 1
        await bot.delete_message(user_id, callback_query.message.message_id) 
        await bot.send_message(user_id, f'<b>{text}</b>', reply_markup=keyboard, parse_mode='html')
    else:
        keyboard = InlineKeyboardMarkup(row_width=1)           
        keyboard.add(InlineKeyboardButton("↩️Вернуться в профиль", callback_data=f"profile:{user_id}"))          
        await bot.delete_message(user_id, callback_query.message.message_id) 
        await bot.send_message(user_id, '<b>❌В данный момент у вас нет игр</b>', reply_markup=keyboard, parse_mode='html')        
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'hack_done')
async def hack_done(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return   
    if cursor2.execute("SELECT type FROM programs WHERE user_id = ?", (user_id,)).fetchone() != ('hack',):
        await bot.send_message(user_id, f"<b>❌Действие недоступно</b>", parse_mode='html')     
        return  
    
    cursor2.execute("SELECT price FROM programs WHERE user_id = ?", (user_id,))   
    price = cursor2.fetchone()[0]
    price = float(price)
    cursor2.execute("DELETE FROM programs WHERE user_id = ?", (user_id,))
    conn2.commit()   
    keyboard = InlineKeyboardMarkup(row_width=1)           
    keyboard.add(InlineKeyboardButton("↩️Вернуться в профиль", callback_data=f"profile:{user_id}"))     
    cursor.execute("UPDATE users SET toncoin = toncoin + ? WHERE user_id = ?", (price, user_id))       
    await bot.send_message(user_id, f"<b>👍Задача сдана, на баланс начислено {price} TON</b>", reply_markup=keyboard, parse_mode='html')        
    conn.commit()    
    await bot.delete_message(user_id, callback_query.message.message_id) 
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'go_to_bed')
async def go_to_bed(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return    
    cursor.execute("UPDATE users SET status = ? WHERE user_id = ?", ('спит', user_id))
    conn.commit()    
    cursor2.execute("SELECT name FROM programs WHERE user_id = ?", (user_id,))
    result = cursor2.fetchone()
    if result:
        cursor2.execute("UPDATE programs SET status = ? WHERE user_id = ?", ('no', user_id))
        conn2.commit()

    await bot.delete_message(user_id, callback_query.message.message_id)    
    await cmd_profile(types.CallbackQuery(data=f"profile:{user_id}"))
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'awake')
async def awake(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return    
    cursor.execute("UPDATE users SET status = ? WHERE user_id = ?", ('бездельничает', user_id))
    conn.commit()       
    await bot.delete_message(user_id, callback_query.message.message_id)    
    await cmd_profile(types.CallbackQuery(data=f"profile:{user_id}"))   
      
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'promo')
async def promo(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("❌Отмена", callback_data=f"profile:{user_id}"))
    await bot.send_message(user_id, '<b>Введите промокод:</b>', reply_markup=keyboard, parse_mode='html')
    cursor.execute("UPDATE users SET flag = ? WHERE user_id = ?", ('promo', user_id))
    conn.commit()   
    await bot.delete_message(user_id, callback_query.message.message_id)  
    
@dp.message_handler(lambda message: message.text and cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (message.chat.id,)).fetchone() and cursor.execute("SELECT flag FROM users WHERE user_id = ?", (message.chat.id,)).fetchone()[0] == 'promo')
async def promo_check(message: types.Message):
    user_id = message.chat.id
    text = message.text
    cursor3.execute("SELECT value, type FROM proms WHERE name = ?", (text,))
    result = cursor3.fetchone()
    keyboard = InlineKeyboardMarkup(row_width=1)           
    keyboard.add(InlineKeyboardButton("↩️Вернуться в профиль", callback_data=f"profile:{user_id}")) 
    if result:
        with open(f"{text}.txt") as proms:
            lines = [line.rstrip() for line in proms]        
        if str(user_id) not in lines:
            cursor3.execute("SELECT count FROM proms WHERE name = ?", (text,))
            result2 = cursor3.fetchone()[0]            
            if result2 == 0:
                cursor3.execute("DELETE FROM proms WHERE name = ?", (text,))
                conn3.commit() 
                os.remove(f"{text}.txt")   
                await bot.send_message(user_id, f"<b>❌Такого промокода не существует или у него закончились активации</b>", parse_mode='html')
                await bot.send_message(admin_id, f"<b>Промокод: {text} закончился</b>", parse_mode='html')                 
            else:
                cursor3.execute("UPDATE proms SET count = count - 1 WHERE name = ?", (text,))
                conn3.commit()
                proms = open(f"{text}.txt", 'a')
                proms.write(str(user_id))
                proms.write('\n')
                proms.close()                
                if result[1] == 'ton':
                    cursor.execute("UPDATE users SET toncoin = toncoin + ? WHERE user_id = ?", (float(result[0]), user_id))
                    conn.commit()
                    await bot.send_message(user_id, f"<b>✅На ваш баланс зачислено {result[0]} TON</b>", reply_markup=keyboard, parse_mode='html')               
                elif result[1] == 'skill':
                    cursor.execute("UPDATE users SET skill = skill + ? WHERE user_id = ?", (int(result[0]), user_id))
                    conn.commit()
                    await bot.send_message(user_id, f"<b>✅Навык персонажа увеличен на {result[0]}</b>", reply_markup=keyboard, parse_mode='html') 
        else:
            await bot.send_message(user_id, "<b>❌Вы уже активировали этот промокод</b>", reply_markup=keyboard, parse_mode='html')                          
    else:
        await bot.send_message(user_id, "<b>❌Такого промокода не существует или у него закончились активации</b>", reply_markup=keyboard, parse_mode='html')        
   
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'profile')
async def cmd_profile(callback_query: types.CallbackQuery):
    global programsdict    
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return    
    if user_id in programsdict:
        del programsdict[user_id]    
    cursor.execute("UPDATE users SET flag = ? WHERE user_id = ?", ('empty', user_id))
    conn.commit()
    cursor.execute("SELECT telegram_name, energy, health, hunger, status, rep, ruble, dollar, toncoin, exchange, skill, computer, flag FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        telegram_name, energy, health, hunger, status, rep, ruble, dollar, toncoin, exchange, skill, computer, flag = result
        computer = technic_products[computer][0]
        keyboard = InlineKeyboardMarkup(row_width=1)        
        if status == 'спит':
            keyboard.add(
            InlineKeyboardButton("🛏Проснуться", callback_data=f"awake:{user_id}"),
            InlineKeyboardButton("🔄Обновить", callback_data=f"profile:{user_id}")
            )  
        else:
            keyboard.add(
            InlineKeyboardButton("💱Обменять деньги", callback_data=f"exchange_money:{user_id}"),
            InlineKeyboardButton("🛍Магазин", callback_data=f"shop:{user_id}"),
            InlineKeyboardButton("📋Мои задачи", callback_data=f"program_status:{user_id}"),
            InlineKeyboardButton("🎮Мои игры", callback_data=f"my_games:{user_id}"),
            InlineKeyboardButton("🛌Спать", callback_data=f"go_to_bed:{user_id}"),
            InlineKeyboardButton("🎲Играть", callback_data=f"play:{user_id}"),
            InlineKeyboardButton("🎁Ввести промокод", callback_data=f"promo:{user_id}"),
            InlineKeyboardButton("🔄Обновить", callback_data=f"profile:{user_id}")
            )
        picture = ''
        if status == 'спит':
            picture = 'sleep'
        elif status == 'бездельничает':
            picture = 'relax'
        else:
            picture = 'work'  
        if user_id in beta_test_users_set:
            picture += '_beta'
        photo = types.InputFile(f"Image/{picture}.jpg")
        await bot.send_photo(user_id, photo, 
            caption=f"<b>🖼ПРОФИЛЬ:</b>\n\n😸Имя: {telegram_name}\n📈Репутация: {rep}\n⚙️Статус: {status}\n\n💻Ноутбук: {computer}\n📕Навык: {skill}\n\n💳Рубли: {round(ruble, 2)}\n💲Доллары: {round(dollar, 5)}\n🪙TON: {round(toncoin, 5)}\n\n⚡️Энергия: {energy}\n❤️Здоровье: {health}\n🤤Сытость: {hunger}",
            parse_mode='html',
            reply_markup=keyboard
        )
        try:
            await bot.delete_message(user_id, callback_query.message.message_id)
        except:
            pass
    else:
        await bot.send_message(user_id, "Вы не зарегистрированы. Используйте /start, чтобы начать игру.")
        try:
            await bot.delete_message(user_id, callback_query.message.message_id)
        except:
            pass
        
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'exchange_money')
async def process_exchange_money_m(callback_query: types.CallbackQuery):
    await process_exchange_money(callback_query)

@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'play')
async def play(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("❌Отмена", callback_data=f"profile:{user_id}"))
    await bot.send_message(user_id, f"<b>Стоимость всех игр: 1 TON</b>\n\n<b>Вы можете играть в игры, отправляя боту эмоджи:</b>\n<code>🎲</code>, <code>🎯</code>, <code>🎳</code>, <code>🏀</code>, <code>⚽</code> и <code>🎰</code>\n\n<b><i>Джекпоты:</i></b>\n⚽ - 1.5 TON\n🏀 - 2 TON\n🎲 - 5 TON\n🎯 - 5 TON\n🎳 - 5 TON\n🎰 - 40 или 5 TON", reply_markup=keyboard, parse_mode='html')
    cursor.execute("UPDATE users SET flag = ? WHERE user_id = ?", ('play', user_id))
    conn.commit()   
    await bot.delete_message(user_id, callback_query.message.message_id)  
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'play_again')
async def play_again(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return    
    cursor.execute("UPDATE users SET flag = ? WHERE user_id = ?", ('play', user_id))
    conn.commit()   
    await bot.delete_message(user_id, callback_query.message.message_id)  
    
@dp.message_handler(content_types=['any'])
async def emoji_message(message: types.Message):
    user_id = message.chat.id 
    if cursor.execute("SELECT flag FROM users WHERE user_id = ?", (message.chat.id,)).fetchone()[0] == 'play':
        flag = 0
        try:
            if message["forward_origin"] != None:
                flag = 1
        except:
            pass
        try:
            if flag == 1:
                keyboard = InlineKeyboardMarkup(row_width=1)
                keyboard.add(InlineKeyboardButton("🖼Перейти в профиль", callback_data=f"profile:{user_id}"))
                keyboard.add(InlineKeyboardButton("🕹Сыграть", callback_data=f"play_again:{user_id}"))                
                await bot.send_message(user_id, "<b>❌Нельзя пересылать сообщения для игры</b>", reply_markup=keyboard, parse_mode='html')                
            elif cursor.execute("SELECT toncoin FROM users WHERE user_id = ?", (message.chat.id,)).fetchone()[0] >= 1:
                keyboard = InlineKeyboardMarkup(row_width=1)
                keyboard.add(InlineKeyboardButton("❌Закончить игру", callback_data=f"profile:{user_id}"))
                emoji = ord(message.dice.emoji)  
                cursor.execute("UPDATE users SET toncoin = toncoin - 1 WHERE user_id = ?", (user_id,))  
                if message.dice.value in emoji_dict[emoji][0]:
                    prize = emoji_dict[emoji][1]
                    if emoji == 127920 and message.dice.value in emoji_dict[emoji][0][1:]:
                        prize = emoji_dict[emoji][2]
                    await asyncio.sleep(2)
                    await bot.send_message(user_id, f"<b>🎉{random.choice(good_news)}\n{prize} TON зачислено на баланс</b>", reply_markup=keyboard, parse_mode=  'html')
                    cursor.execute("UPDATE users SET toncoin = toncoin + ? WHERE user_id = ?", (prize, user_id))            
                else:
                    await asyncio.sleep(2)
                    await bot.send_message(user_id, f"<b>😿{random.choice(bad_news)}</b>", reply_markup=keyboard, parse_mode='html')
                conn.commit()
            else:
                await bot.send_message(user_id, f"<b>❌Нехватает средств для игры</b>", parse_mode='html')                
        except:
            await bot.send_message(user_id, "<b>❌Некорректный ввод</b>", parse_mode='html')
    else:   
        if cursor.execute("SELECT status FROM users WHERE user_id = ?", (user_id,)).fetchone()[0] == 'выбыл':
            await bot.send_message(user_id, "<b>📌Ваш персонаж мёртв, начните новую игру:\n\nНажмите: /start</b>", parse_mode='html')
            return True
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton("🖼Перейти в профиль", callback_data=f"profile:{user_id}"))        
        await bot.send_message(user_id, "<b>🤷‍♂️Не могу распознать команду, попробуйте начать заново, перейдите в профиль</b>", reply_markup=keyboard, parse_mode='html')
    
if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
