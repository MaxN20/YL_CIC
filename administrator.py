import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ContentType
from aiogram.types.input_file import InputFile
from config import good_news, bad_news, moneydict, channel_name
from config import admin_id, admin_balance_flag, admin_user_flag, admin_promo_flag, admin_promo_info_flag, admin_mailing, text_mail, ton_for_sub_flag, list_of_good_users
from config import API_TOKEN, bot, dp
from config import bd_1, bd_2, bd_3, conn, cursor, conn2, cursor2, conn3, cursor3

async def admin(message: types.Message):
    user_id = message.from_user.id
    if admin_id == user_id:
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("💰Пополнить баланс", callback_data=f"admin_balance:{user_id}"),
            InlineKeyboardButton("🔖Создать промокод", callback_data=f"admin_promo:{user_id}"),    
            InlineKeyboardButton("ℹ️Данные по промокодам", callback_data=f"admin_promo_info:{user_id}"),  
            InlineKeyboardButton("📄Данные по пользователю", callback_data=f"admin_user:{user_id}"),
            InlineKeyboardButton("📦Выгрузить БД", callback_data=f"admin_bd:{user_id}"),
            InlineKeyboardButton("📠Запустить рассылку", callback_data=f"admin_mailing:{user_id}"),
            InlineKeyboardButton("🤝TON for SUB", callback_data=f"ton_for_sub:{user_id}")
        ) 
        await bot.send_message(user_id, "Выберите действие:", reply_markup=keyboard)
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'admin_cancel')
async def admin_balance(callback_query: types.CallbackQuery):
    global admin_balance_flag
    global admin_user_flag
    global admin_promo_flag 
    global admin_promo_info_flag
    global admin_mailing
    global text_mail
    global ton_for_sub_flag    
    global list_of_good_users
    user_id = int(callback_query.data.split(':')[1])
    admin_balance_flag = 0
    admin_user_flag = 0
    admin_promo_flag = 0 
    admin_promo_info_flag = 0
    admin_mailing = 0
    text_mail = ''
    ton_for_sub_flag = 0
    list_of_good_users = set()
    try:
        os.remove('Image/mail_photo.jpg')
    except OSError:
        pass   
    await bot.send_message(user_id, "✅Все флаги сброшены") 
    await bot.delete_message(user_id, callback_query.message.message_id)    

@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'admin_balance')
async def admin_balance(callback_query: types.CallbackQuery):
    global admin_balance_flag
    user_id = int(callback_query.data.split(':')[1])
    admin_balance_flag = 1
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("❌Отмена", callback_data=f"admin_cancel:{user_id}"))    
    await bot.send_message(user_id, "Введите: {id} {TON}(через пробел)\n\nid - Пользователь которому пополнить баланс TON\nTON - количество монет", reply_markup=keyboard) 
    await bot.delete_message(user_id, callback_query.message.message_id)    
    
@dp.message_handler(lambda message: message.text and len(message.text.split()) == 2 and message.chat.id == admin_id and admin_balance_flag == 1)
async def admin_balance_2(message: types.Message):
    global admin_balance_flag
    user_id = message.chat.id
    admin_balance_flag = 0
    try:
        idi, ton = int(message.text.split()[0]), float(message.text.split()[1])
        cursor.execute("SELECT telegram_name FROM users WHERE user_id = ?", (idi,))
        result = cursor.fetchone()
        if result:
            cursor.execute("UPDATE users SET toncoin = toncoin + ? WHERE user_id = ?", (ton, idi))
            conn.commit()    
            await bot.send_message(idi, f"<b>💸На баланс начислено: {ton} TON</b>", parse_mode='html')             
            await bot.send_message(user_id, f"Пользователь {result[0]} с id - {idi} получил {ton} TON") 
        else:
            await bot.send_message(user_id, f"Пользователя с id - {idi} НЕТ")
    except:
        await bot.send_message(user_id, "Некоректный ввод данных")                
         
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'admin_user')
async def admin_user(callback_query: types.CallbackQuery):
    global admin_user_flag
    user_id = int(callback_query.data.split(':')[1])
    admin_user_flag = 1
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("❌Отмена", callback_data=f"admin_cancel:{user_id}"))    
    await bot.send_message(user_id, "Введите: {id}\n\nid - Пользователь по которому хотите получить информацию", reply_markup=keyboard) 
    await bot.delete_message(user_id, callback_query.message.message_id)          
     
@dp.message_handler(lambda message: message.text and message.chat.id == admin_id and admin_user_flag == 1)
async def admin_user_2(message: types.Message):
    global admin_user_flag
    user_id = message.chat.id
    idi = message.text
    admin_user_flag = 0
    try:
        idi = int(idi)
        cursor.execute("SELECT telegram_name, energy, health, hunger, status, rep, ruble, dollar, toncoin, exchange, skill, computer, flag FROM users WHERE user_id = ?", (idi,))
        result = cursor.fetchone()
        if result:
            telegram_name, energy, health, hunger, status, rep, ruble, dollar, toncoin, exchange, skill, computer, flag = result
            ruble, dollar, toncoin = round(ruble, 5), round(dollar, 5), round(toncoin, 5)
            await bot.send_message(user_id, f"😸Имя: {telegram_name}\n📈Репутация: {rep}\n⚙️Статус: {status}\n\n💻Ноутбук: {computer}\n📕Навык: {skill}\n\n💳Рубли: {ruble}\n💲Доллары: {dollar}\n🪙TON: {toncoin}\n\n⚡️Энергия: {energy}\n❤️Здоровье: {health}\n🤤Сытость: {hunger}",
            parse_mode='html')
        else:
            await bot.send_message(user_id, f"Пользователя с id - {idi} НЕТ")
    except:
        await bot.send_message(user_id, "Некоректный ввод данных") 
     
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'admin_promo')
async def admin_promo(callback_query: types.CallbackQuery):
    global admin_promo_flag
    user_id = int(callback_query.data.split(':')[1])
    admin_promo_flag = 1
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("❌Отмена", callback_data=f"admin_cancel:{user_id}"))    
    await bot.send_message(user_id, "Введите: {name} {value} {count} {type}(через пробел)\n\nname - сам промокод\nvalue - количество {type} при использовании\ncount - количество активаций\ntype - вид (ton, skill)", reply_markup=keyboard) 
    await bot.delete_message(user_id, callback_query.message.message_id) 
     
@dp.message_handler(lambda message: message.text and len(message.text.split()) == 4 and message.chat.id == admin_id and admin_promo_flag == 1)
async def admin_promo_2(message: types.Message):
    global admin_promo_flag
    user_id = message.chat.id
    admin_promo_flag = 0
    data = message.text.split()    
    try:
        name, value, count, typee = data[0], float(data[1]), int(data[2]), data[3]
        if data[3] not in ['ton', 'skill']:
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(InlineKeyboardButton("❌Отменить создание промокода", callback_data=f"admin_cancel:{user_id}"))            
            await bot.send_message(user_id, f"Неверное значение параметра type", reply_markup=keyboard)
            return
        cursor3.execute("SELECT name FROM proms WHERE name = ?", (name,))
        result = cursor3.fetchone()
        if result:
            await bot.send_message(user_id, "Такой промокод уже существует")     
        else:
            open(f"{name}.txt", 'w').close()
            cursor3.execute("INSERT OR IGNORE INTO proms (name, value, count, type) VALUES (?, ?, ?, ?)", (name, value, count, typee))
            conn3.commit()
            await bot.send_message(user_id, f"Промокод {name} создан")                 
    except:
        await bot.send_message(user_id, "Некоректный ввод данных")     
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'admin_promo_info')
async def admin_promo_info(callback_query: types.CallbackQuery):
    global admin_promo_info_flag
    user_id = int(callback_query.data.split(':')[1])
    admin_promo_info_flag = 1
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("❌Отмена", callback_data=f"admin_cancel:{user_id}"))    
    await bot.send_message(user_id, "Введите: {name}\n\nname - название интересующего промокод", reply_markup=keyboard) 
    await bot.delete_message(user_id, callback_query.message.message_id) 
    
@dp.message_handler(lambda message: message.text and message.chat.id == admin_id and admin_promo_info_flag == 1)
async def admin_promo_info_2(message: types.Message):
    global admin_promo_info_flag
    admin_promo_info_flag = 0
    user_id = message.chat.id
    cursor3.execute("SELECT value, count, type FROM proms WHERE name = ?", (message.text,))
    result = cursor3.fetchone()
    if result:
        await bot.send_message(user_id, f"Промокод на: {result[0]} {result[2]}\nОсталось активаций: {result[1]}")     
    else:
        await bot.send_message(user_id, "Такого промокода нет")     
                 
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'admin_bd')
async def admin_bd(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(':')[1])   
    await bot.send_document(chat_id = admin_id, document = InputFile(bd_1), caption = '😺Пользователи😺')
    await bot.send_document(chat_id = admin_id, document = InputFile(bd_2), caption = '💾Программы💾')
    await bot.send_document(chat_id = admin_id, document = InputFile(bd_3), caption = '🎁Промокоды🎁')
    await bot.delete_message(admin_id, callback_query.message.message_id) 
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'admin_mailing')
async def admin_mailing(callback_query: types.CallbackQuery):
    global admin_mailing
    user_id = int(callback_query.data.split(':')[1])
    admin_mailing = 1
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("❌Отмена", callback_data=f"admin_cancel:{user_id}"))      
    await bot.send_message(user_id, 'Сначала отправьте фото(если оно будет), а потом текст рассылки:\n\n<b>текст</b> - жирный\n<i>текст</i> - курсив\n<code>текст</code> - моноширинный\n<a href="https://ya.ru/">текст</a> - ссылка (https://ya.ru/)\n[line]кнопка-ссылка[/line] - Кнопка', reply_markup=keyboard, disable_web_page_preview = True) 
    await bot.delete_message(user_id, callback_query.message.message_id)   
    
@dp.message_handler(content_types=ContentType.PHOTO)
async def process_mail_photo(message: types.Message):
    if admin_mailing == 1:  
        await message.photo[-1].download('Image/mail_photo.jpg')
        await bot.send_message(admin_id, 'Фото сохранено') 
        
@dp.message_handler(lambda message: message.text and message.chat.id == admin_id and admin_mailing == 1)
async def admin_mailing_2(message: types.Message):
    global admin_mailing
    global text_mail
    user_id = message.chat.id
    admin_mailing = 0
    text_mail = message.text
    inline = ''
    inline_text = ''
    inline_link = ''
    edit_text = text_mail        
    
    if '[line]' in text_mail and '[/line]' in text_mail:
        inline = text_mail[text_mail.index('[line]') + 6:text_mail.index('[/line]')]
        if '-' in inline:
            inline_text = inline[:inline.index('-')]
            inline_link = inline[inline.index('-') + 1:]
            edit_text = text_mail[:text_mail.index('[line]')]
        else:
            await bot.send_message(user_id, 'Символ "-" не найден в сообщении')  
    else:
        await bot.send_message(user_id, 'Url-кнопка не найдена сообщении')  
            
    keyboard = InlineKeyboardMarkup(row_width=2)
    if inline_text != '':        
        keyboard.add(InlineKeyboardButton(inline_text, url=inline_link))
        
    keyboard.add(InlineKeyboardButton("✅Всё верно", callback_data=f"admin_mailing_3:{user_id}"))        
    keyboard.add(InlineKeyboardButton("❌Отмена", callback_data=f"admin_cancel:{user_id}"))
    
    try:
        if os.path.isfile('Image/mail_photo.jpg'):
            photo = InputFile('Image/mail_photo.jpg')            
            await bot.send_photo(chat_id=user_id, photo=photo, caption=edit_text, reply_markup=keyboard, parse_mode='html')            
        else:
            await bot.send_message(user_id, edit_text, reply_markup=keyboard, parse_mode='html', disable_web_page_preview = True)
    except Exception as e:
        text_mail = ''
        await bot.send_message(user_id, e)               
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'admin_mailing_3')
async def admin_mailing_3(callback_query: types.CallbackQuery):
    global text_mail
    user_id = int(callback_query.data.split(':')[1])
    cursor.execute("SELECT user_id FROM users")
    result = [j[0] for j in cursor]
    good = 0
    bad = 0
    
    inline = ''
    inline_text = ''
    inline_link = ''
    if '[line]' in text_mail and '[/line]' in text_mail:
        inline = text_mail[text_mail.index('[line]') + 6:text_mail.index('[/line]')]
        if '-' in inline:
            inline_text = inline[:inline.index('-')]
            inline_link = inline[inline.index('-') + 1:]
            text_mail = text_mail[:text_mail.index('[line]')]
    keyboard = InlineKeyboardMarkup(row_width=1)
    if inline_text != '':        
        keyboard.add(InlineKeyboardButton(inline_text, url=inline_link))
        for i in result:
            try:
                if os.path.isfile('Image/mail_photo.jpg'):
                    photo = InputFile('Image/mail_photo.jpg')            
                    await bot.send_photo(chat_id=i, photo=photo, caption=text_mail, reply_markup=keyboard, parse_mode='html')            
                else:
                    await bot.send_message(i, text_mail, reply_markup=keyboard, parse_mode='html', disable_web_page_preview = True)                
                good += 1
            except:
                bad += 1
    else:
        for i in result:
            try:
                if os.path.isfile('Image/mail_photo.jpg'):
                    photo = InputFile('Image/mail_photo.jpg')            
                    await bot.send_photo(chat_id=i, photo=photo, caption=text_mail, parse_mode='html', disable_web_page_preview = True)            
                else:
                    await bot.send_message(i, text_mail, parse_mode='html', disable_web_page_preview = True)                   
                good += 1
            except:
                bad += 1
                
    await bot.send_message(admin_id, f"Успешно: {good}\nНеудачно: {bad}")     
    text_mail = ''
    await bot.delete_message(user_id, callback_query.message.message_id)       
    
@dp.callback_query_handler(lambda c: c.data.split(':')[0] == 'ton_for_sub')
async def ton_for_sub(callback_query: types.CallbackQuery):
    global ton_for_sub_flag
    global list_of_good_users
    await bot.send_message(admin_id, f'Поиск хороших пользователей начат')         
    rows = cursor.execute("SELECT user_id FROM users")
    tables = [row[0] for row in rows]
    for idi in tables:
        user_channel_status = await bot.get_chat_member(chat_id=channel_name, user_id=idi)
        if user_channel_status["status"] != 'left':
            list_of_good_users.add(idi)
    ton_for_sub_flag = 1
    await bot.delete_message(admin_id, callback_query.message.message_id)           
    await bot.send_message(admin_id, f'Количество найденых пользователей: {len(list_of_good_users)}\n\nВведите количество TON, для каждого "хорошего" пользователя')     
    
@dp.message_handler(lambda message: message.text and message.chat.id == admin_id and ton_for_sub_flag == 1)
async def ton_for_sub_2(message: types.Message):
    global ton_for_sub_flag
    global list_of_good_users
    value = float(message.text)
    for idi in list_of_good_users:
        try:
            cursor.execute("UPDATE users SET toncoin = toncoin + ? WHERE user_id = ?", (value, idi))        
            await bot.send_message(idi, f"<b>💸На баланс начислено: {value} TON\n😻Спасибо, что вы подписаны на {channel_name}</b>", parse_mode='html')
        except:
            pass
    conn.commit()    
    ton_for_sub_flag = 0
    list_of_good_users = set()
    await bot.send_message(admin_id, f"Все пользователи, подписанные на {channel_name}, получили {value} TON")     
