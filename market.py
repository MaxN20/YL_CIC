from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from Resources.food_shop import food_products
from Resources.health_shop import health_products
from Resources.technic_shop import technic_products
from Resources.skill_shop import skill_products
from config import API_TOKEN, bot, dp
from config import bd_1, bd_2, bd_3, conn, cursor, conn2, cursor2, conn3, cursor3  

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

async def shop(callback_query):
    user_id = int(callback_query.data.split(':')[1])    
    if await check_life(user_id, callback_query):
        return
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🛒Еда", callback_data=f"food:{user_id}"),
        InlineKeyboardButton("🌡Здоровье", callback_data=f"health:{user_id}"),
        InlineKeyboardButton("💻Техника", callback_data=f"technic:{user_id}"),
        InlineKeyboardButton("💡Навык", callback_data=f"skill:{user_id}"),
        InlineKeyboardButton("🖼Вернуться в профиль", callback_data=f"profile:{user_id}")
    ) 
    await bot.send_message(user_id, "<b>Выберите категорию:</b>", reply_markup=keyboard, parse_mode='html')
    await bot.delete_message(user_id, callback_query.message.message_id)

@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'skill')
async def food_shop(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return    
    cursor.execute("SELECT skill, ruble FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()  
    skill, ruble = result
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    for i in skill_products:
        line = skill_products[i]
        keyboard.add(
        InlineKeyboardButton(f"{line[0]} - {line[2]['price']} (🧰: {line[2]['value']})", callback_data=f"buy_skill:{i}:{user_id}")
        )       
        
    keyboard.add(InlineKeyboardButton("❌Отмена", callback_data=f"profile:{user_id}"))

    await bot.send_message(user_id, f"<b>Баланс:</b>\n{round(ruble, 2)} ₽\n\n<b>🧰Навык персонажа: {skill}</b>\n\n<b>Выберите для покупки:</b>", reply_markup=keyboard, parse_mode='html')
    await bot.delete_message(user_id, callback_query.message.message_id)

@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'buy_skill')
async def buy_skill_product(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[2])
    if await check_life(user_id, callback_query):
        return    
    product = callback_query.data.split(':')[1]
    product = skill_products[product]
    if check_balance(user_id, product[2]['price']):
        perform_purchase(user_id, price=product[2]['price'], skill=product[2]['value'])
        await bot.delete_message(user_id, callback_query.message.message_id)            
        await bot.send_message(user_id, f"<b>📕Вы успешно купили {product[0]} за {product[2]['price']}₽ {product[1]}</b>", parse_mode='html')
        await check_all_values(user_id)
            
    else:
        await bot.send_message(user_id, "<b>❌У вас недостаточно средств для покупки</b>", parse_mode='html')
        await bot.delete_message(user_id, callback_query.message.message_id)

    await cmd_profile(types.CallbackQuery(data=f"profile:{user_id}"))

@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'food')
async def food_shop(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return    
    cursor.execute("SELECT energy, health, hunger, ruble FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()  
    energy, health, hunger, ruble = result
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    for i in food_products:
        line = food_products[i]
        keyboard.add(
        InlineKeyboardButton(f"{line[0]} - {line[2]['price']} (🤤: {line[2]['satiety']} ❤️: {line[2]['health']} ⚡️: {line[2]['energy']})", callback_data=f"buy_food:{i}:{user_id}")
        )       
        
    keyboard.add(InlineKeyboardButton("❌Отмена", callback_data=f"profile:{user_id}"))

    await bot.send_message(user_id, f"<b>Баланс:</b>\n{round(ruble, 2)} ₽\n\n<b>Состояние персонажа:</b>\n⚡️Энергия: {energy}\n❤️Здоровье: {health}\n🤤Сытость: {hunger}\n\n<b>Выберите продукт для покупки:</b>", reply_markup=keyboard, parse_mode='html')
    await bot.delete_message(user_id, callback_query.message.message_id)

@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'buy_food')
async def buy_food_product(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[2])
    if await check_life(user_id, callback_query):
        return    
    product = callback_query.data.split(':')[1]
    product = food_products[product]
    if check_balance(user_id, product[2]['price']):
        perform_purchase(user_id, price=product[2]['price'], satiety=product[2]['satiety'], health=product[2]['health'], energy=product[2]['energy'])
        await bot.delete_message(user_id, callback_query.message.message_id)            
        await bot.send_message(user_id, f"<b>🤤Вы успешно купили {product[0]} за {product[2]['price']}₽ {product[1]}</b>", parse_mode='html')
        await check_all_values(user_id)
            
    else:
        await bot.send_message(user_id, "<b>❌У вас недостаточно средств для покупки</b>", parse_mode='html')
        await bot.delete_message(user_id, callback_query.message.message_id)

    await cmd_profile(types.CallbackQuery(data=f"profile:{user_id}"))

@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'health')
async def health_shop(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return    
    cursor.execute("SELECT energy, health, ruble FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()  
    energy, health, ruble = result
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    for i in health_products:
        line = health_products[i]
        keyboard.add(
        InlineKeyboardButton(f"{line[0]} - {line[2]['price']} (❤️: {line[2]['health']} ⚡️: {line[2]['energy']})", callback_data=f"buy_health:{i}:{user_id}")
        )       
        
    keyboard.add(InlineKeyboardButton("❌Отмена", callback_data=f"profile:{user_id}"))

    await bot.send_message(user_id, f"<b>Баланс:</b>\n{round(ruble, 2)} ₽\n\n<b>Состояние персонажа:</b>\n⚡️Энергия: {energy}\n❤️Здоровье: {health}\n\n<b>Выберите продукт для покупки:</b>", reply_markup=keyboard, parse_mode='html')
    await bot.delete_message(user_id, callback_query.message.message_id)

@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'buy_health')
async def buy_health_product(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[2])
    if await check_life(user_id, callback_query):
        return    
    product = callback_query.data.split(':')[1]
    product = health_products[product]
    if check_balance(user_id, product[2]['price']):
        perform_purchase(user_id, price=product[2]['price'], satiety=product[2]['satiety'], health=product[2]['health'], energy=product[2]['energy'])
        await bot.send_message(user_id, f"<b>❤️Вы успешно купили {product[0]} за {product[2]['price']}₽ {product[1]}</b>", parse_mode='html')
        await bot.delete_message(user_id, callback_query.message.message_id)
        await check_all_values(user_id)
            
    else:
        await bot.send_message(user_id, "<b>❌У вас недостаточно средств для покупки</b>", parse_mode='html')
        await bot.delete_message(user_id, callback_query.message.message_id)

    await cmd_profile(types.CallbackQuery(data=f"profile:{user_id}"))

@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'technic')
async def technic_shop(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])
    if await check_life(user_id, callback_query):
        return    
    cursor.execute("SELECT ruble, computer FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()  
    ruble, computer = result
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    level = 1
    flag = 0
    for i in technic_products:
        if flag == 1:
            line = technic_products[i]
            keyboard.add(
            InlineKeyboardButton(f"{line[0]} - {line[2]['price']} ({level} Уровень)", callback_data=f"buy_technic:{i}:{user_id}")
            )   
        if i == computer:
            flag = 1        
        level += 1
    if i == computer:
        keyboard.add(InlineKeyboardButton("❗️У вас максимальный уровень ноутбука❗️", callback_data=f"profile:{user_id}"))
    keyboard.add(InlineKeyboardButton("❌Отмена", callback_data=f"profile:{user_id}"))

    await bot.send_message(user_id, f"<b>Баланс:</b>\n{round(ruble, 2)} ₽\n\n<b>Выберите продукт для покупки:</b>", reply_markup=keyboard, parse_mode='html')
    await bot.delete_message(user_id, callback_query.message.message_id)

@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'buy_technic')
async def buy_technic_product(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[2])
    if await check_life(user_id, callback_query):
        return    
    product = callback_query.data.split(':')[1]
    comp = product
    product = technic_products[product]
    
    if check_balance(user_id, product[2]['price']): 
        cursor.execute("SELECT computer FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        sell_product = technic_products[result[0]]
        await bot.send_message(user_id, f"<b>💸Вы продали свой старый ноутбук {sell_product[0]} за {round(sell_product[2]['price'] / 2, 1)}₽ {sell_product[1]}</b>", parse_mode='html')
        cursor.execute("UPDATE users SET ruble = ruble + ? WHERE user_id = ?", (round(sell_product[2]['price'] / 2, 1), user_id))
        conn.commit()
        perform_purchase(user_id, price=product[2]['price'], computer=comp)        
        await bot.send_message(user_id, f"<b>💻Вы успешно купили {product[0]} за {product[2]['price']}₽ {product[1]}</b>", parse_mode='html')
        await bot.delete_message(user_id, callback_query.message.message_id)
        await check_all_values(user_id)
            
    else:
        await bot.send_message(user_id, "<b>❌У вас недостаточно средств для покупки</b>", parse_mode='html')
        await bot.delete_message(user_id, callback_query.message.message_id)

    await cmd_profile(types.CallbackQuery(data=f"profile:{user_id}"))

def check_balance(user_id, amount):
    cursor.execute("SELECT ruble FROM users WHERE user_id = ?", (user_id,))
    balance = cursor.fetchone()[0]
    return balance >= amount

def perform_purchase(user_id, price, satiety=0, health=0, energy=0, computer='', skill=''):
    total_minus = 0
    cursor.execute("SELECT energy, health, hunger, computer FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    energy_real, health_real, hunger_real, computer_real = result
    if computer == '':
        computer = computer_real 
    if energy_real + energy < 0:
        energy = -energy_real
        total_minus += -(energy_real + energy)
    if health_real + health < 0:
        health = -health_real
        total_minus += -(health_real + health)
    if hunger_real + satiety < 0:
        satiety = -hunger_real
        total_minus += -(hunger_real + satiety)        
    
    cursor.execute("UPDATE users SET ruble = ruble - ?, hunger = hunger + ?, health = health + ?, energy = energy + ?, computer = ?, skill = skill + ? WHERE user_id = ?", (round(price, 2), satiety, health - total_minus, energy, computer, skill, user_id))
    conn.commit()
    
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'profile')
async def cmd_profile(callback_query: types.CallbackQuery):
    from main import cmd_profile
    await cmd_profile(callback_query)
