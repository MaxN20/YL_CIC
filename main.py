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
        elif status == 'безделничает':
            picture = 'relax'
        else:
            picture = 'work'  
        if user_id in beta_test_users_set:
            picture += '_beta'
        photo = types.InputFile(f"{picture}.jpg")
        await bot.send_photo(user_id, photo, 
            caption=f"<b>🖼ПРОФИЛЬ:</b>\n\n😸Имя: {telegram_name}\n📈Репутация: {rep}\n⚙️Статус: {status}\n\n💻Ноутбук: {computer}\n📕Навык: {skill}\n\n💳Рубли: {round(ruble, 5)}\n💲Доллары: {round(dollar, 5)}\n🪙TON: {round(toncoin, 5)}\n\n⚡️Энергия: {energy}\n❤️Здоровье: {health}\n🤤Сытость: {hunger}",
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
