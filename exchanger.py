from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import API_TOKEN, bot, dp
from config import bd_1, bd_2, bd_3, conn, cursor, conn2, cursor2, conn3, cursor3 
from config import moneydict
import requests

async def check_life(user_id, callback_query):
    if cursor.execute("SELECT status FROM users WHERE user_id = ?", (user_id,)).fetchone()[0] == 'выбыл':
        await bot.send_message(user_id, "<b>📌Ваш персонаж мёртв, начните новую игру:\n\nНажмите: /start</b>", parse_mode='html')
        await bot.delete_message(user_id, callback_query.message.message_id)        
        return True

async def process_exchange_money(callback_query):
    user_id = callback_query.data.split(':')[1]
    if await check_life(user_id, callback_query):
        return    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Рубль ➡️ Доллар", callback_data=f"exchange_step2:rub2usd:{user_id}"), InlineKeyboardButton("Рубль ➡ ️TON", callback_data=f"exchange_step2:rub2ton:{user_id}"),
        InlineKeyboardButton("Доллар ➡ Рубль️", callback_data=f"exchange_step2:usd2rub:{user_id}"), InlineKeyboardButton("Доллар ➡ TON", callback_data=f"exchange_step2:usd2ton:{user_id}"),
        InlineKeyboardButton("TON ➡ Рубль️", callback_data=f"exchange_step2:ton2rub:{user_id}"), InlineKeyboardButton("TON ➡ ️Доллар", callback_data=f"exchange_step2:ton2usd:{user_id}"),
        InlineKeyboardButton("🖼Вернуться в профиль", callback_data=f"profile:{user_id}")
    )
    
    await bot.delete_message(user_id, callback_query.message.message_id)    
    await bot.send_message(user_id, "<b>💱Выберите валюты для обмена:</b>", reply_markup=keyboard, parse_mode='html')    
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'exchange_step2')
async def process_exchange_money_2(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[2])
    if await check_life(user_id, callback_query):
        return    
    firstv = callback_query.data.split(':')[1].split('2')[0]
    secondv = callback_query.data.split(':')[1].split('2')[1]
    cursor.execute("SELECT ruble, dollar, toncoin FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()    
    ruble, dollar, toncoin = result
    await bot.delete_message(user_id, callback_query.message.message_id)    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("❌Отменить", callback_data=f"profile:{user_id}")
        )    
    await bot.send_message(user_id, f"<b>Ваш кошелёк:</b>\n💳Рубли: <code>{round(ruble, 2)}</code>\n💲Доллары: <code>{round(dollar, 5)}</code>\n🪙TON: <code>{round(toncoin, 5)}</code>\n\n<b>Введите сумму для обмена {moneydict[firstv]} на {moneydict[secondv]}, либо отмените его:</b>", parse_mode='html', reply_markup=keyboard)
    cursor.execute("UPDATE users SET exchange = ?, flag = ? WHERE user_id = ?", (f'{firstv}:{secondv}', 'exchage_flag', user_id))
    conn.commit()    

@dp.message_handler(lambda message: message.text and cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (message.chat.id,)).fetchone() and cursor.execute("SELECT flag FROM users WHERE user_id = ?", (message.chat.id,)).fetchone()[0] == 'exchage_flag')
async def handle_exchange_amount(message: types.Message):
    user_id = message.chat.id
    exchange_amount = message.text.strip()
    try:
        cursor.execute("SELECT exchange FROM users WHERE user_id = ?", (user_id,))
        exchange = cursor.fetchone()
        firstv = exchange[0].split(':')[0]
        secondv = exchange[0].split(':')[1]           
            
        exchange_amount = float(exchange_amount)
            
        if firstv == 'ton':
            data = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies={secondv}").json()
            price = round(data['the-open-network'][secondv], 5)
        elif secondv == 'ton':
            data = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies={firstv}").json()
            price = round(1 / data['the-open-network'][firstv], 5)
        elif firstv == 'rub':
            data = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
            price = round(1 / data['Valute']['USD']['Value'], 5)
        else:
            data = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
            price = round(data['Valute']['USD']['Value'], 5)
            
        keyboard_m = InlineKeyboardMarkup(row_width=2)
        keyboard_m.add(
            InlineKeyboardButton("✅Обменять", callback_data=f"successful_exchange:{user_id}:{exchange_amount}:{firstv}:{round(exchange_amount * price, 5)}:{secondv}"),
            InlineKeyboardButton("❌Отменить", callback_data=f"profile:{user_id}")
        )  
            
        await bot.send_message(user_id, f"<b>👉Вы можете обменять {exchange_amount} {moneydict[firstv]} на {round(exchange_amount * price, 5)} {moneydict[secondv]}</b>", reply_markup=keyboard_m, parse_mode='html')   
            
    except ValueError:
        await bot.send_message(user_id, "<b>❗️Введите корректное числовое значение для обмена</b>", parse_mode='html')   
                              
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'successful_exchange')
async def successful_exchange_money(callback_query: types.CallbackQuery):   
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return    
    value1 = float(callback_query.data.split(':')[2])
    flag1 = callback_query.data.split(':')[3]
    value2 = float(callback_query.data.split(':')[4])
    flag2 = callback_query.data.split(':')[5]
    flag1 = flag1.replace('rub', 'ruble').replace('usd', 'dollar').replace('ton', 'toncoin')
    flag2 = flag2.replace('rub', 'ruble').replace('usd', 'dollar').replace('ton', 'toncoin')
    cursor.execute("SELECT ruble, dollar, toncoin FROM users WHERE user_id = ?", (user_id,))
    ruble_value, dollar_value, toncoin_value = cursor.fetchone()
    if flag2 == 'ruble':
        other_value = ruble_value
    elif flag2 == 'dollar':
        other_value = dollar_value
    else:
        other_value = toncoin_value
        
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🖼Вернуться в профиль", callback_data=f"profile:{user_id}")
    )      
        
    if flag1 == 'ruble':
        if value1 > ruble_value:
            await bot.send_message(user_id, "<b>❌Недостаточно средств для обмена</b>", parse_mode='html') 
        else:
            cursor.execute(f"UPDATE users SET ruble = ?, {flag2} = ? WHERE user_id = ?", 
                           (round(ruble_value - value1, 5), round(other_value + value2, 5), user_id))
            conn.commit()
            await bot.send_message(user_id, "<b>✅Обмен произведён успешно</b>", reply_markup=keyboard, parse_mode='html')       
            
    elif flag1 == 'dollar':
        if value1 > dollar_value:
            await bot.send_message(user_id, "<b>❌Недостаточно средств для обмена</b>", parse_mode='html') 
        else:
            cursor.execute(f"UPDATE users SET dollar = ?, {flag2} = ? WHERE user_id = ?", 
                           (round(dollar_value - value1, 5), round(other_value + value2, 5), user_id))
            conn.commit()
            await bot.send_message(user_id, "<b>✅Обмен произведён успешно</b>", reply_markup=keyboard, parse_mode='html') 
            
    elif flag1 == 'toncoin':
        if value1 > toncoin_value:
            await bot.send_message(user_id, "<b>❌Недостаточно средств для обмена</b>", parse_mode='html') 
        else:    
            cursor.execute(f"UPDATE users SET toncoin = ?, {flag2} = ? WHERE user_id = ?", 
                           (round(toncoin_value - value1, 5), round(other_value + value2, 5), user_id))
            conn.commit()
            await bot.send_message(user_id, "<b>✅Обмен произведён успешно</b>", reply_markup=keyboard, parse_mode='html')
            
    await bot.delete_message(user_id, callback_query.message.message_id)
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'profile')
async def cmd_profile(callback_query: types.CallbackQuery):
    from main import cmd_profile
    await cmd_profile(callback_query)
