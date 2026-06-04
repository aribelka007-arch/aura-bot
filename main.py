import telebot
from telebot import types

TOKEN = '8693012719:AAFFRW4JMaQVmXPIIgkcVLJC-Wwe43Y4vDE'
bot = telebot.TeleBot(TOKEN)

PRICES = {
    "exp": {"name": "⚡ Экспресс-мойка", "costs": [500, 600, 700]},
    "body": {"name": "🚗 Мойка кузова", "costs": [600, 800, 1000]},
    "2ph": {"name": "🧼 Двух-фазная кузова", "costs": [1100, 1400, 1700]},
    "3ph": {"name": "✨ Трёх-фазная кузова", "costs": [1400, 1700, 2000]},
    "mats": {"name": "🧺 Kuзов + коврики", "costs": [700, 1000, 1300]},
    "sal": {"name": "🧽 Кузов + салон", "costs": [1500, 2000, 2500]},
    "wax": {"name": "🕯️ Твердый воск", "costs": [1500, 2000, 2500]},
}

ADDONS = {
    "add_wx": {"name": "Обработка воском", "price": 300},
    "add_qz": {"name": "Обработка кварцем", "price": 600},
    "add_bt": {"name": "Очистка битума (1 дет.)", "price": 200},
    "add_eg": {"name": "Мойка двигателя", "price": 1500},
    "add_pl": {"name": "Полироль пластика", "price": 500},
    "add_lt": {"name": "Кондиционер кожи", "price": 500},
    "add_tr": {"name": "Чернение резины", "price": 300},
    "add_tk": {"name": "Уборка багажника", "price": 500},
}

user_orders = {}

def reset_user(chat_id):
    user_orders[chat_id] = {"type_idx": None, "main_service": None, "addons": []}

@bot.message_handler(commands=['start', 'reset'])
def send_welcome(message):
    reset_user(message.chat.id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🚗 Легковая", callback_data="t_0"),
        types.InlineKeyboardButton("🚙 Кроссовер / Паркетник", callback_data="t_1"),
        types.InlineKeyboardButton("🚐 Минивэн / Микроавтобус", callback_data="t_2")
    )
    bot.send_message(message.chat.id, "👋 Привет! Выбери тип автомобиля для расчета:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("t_"))
def handle_type(call):
    chat_id = call.message.chat.id
    if chat_id not in user_orders: reset_user(chat_id)
    
    type_idx = int(call.data.split("_")[1])
    user_orders[chat_id]["type_idx"] = type_idx
    
    types_names = ["Легковая", "Кроссовер", "Минивэн/Микроавтобус"]
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, item in PRICES.items():
        price = item["costs"][type_idx]
        markup.add(types.InlineKeyboardButton(f"{item['name']} — {price}₽", callback_data=f"m_{key}"))
        
    bot.edit_message_text(f"Выбран тип: *{types_names[type_idx]}*\nТеперь выбери основную услугу:", 
                          chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("m_"))
def handle_main_service(call):
    chat_id = call.message.chat.id
    if chat_id not in user_orders or user_orders[chat_id]["type_idx"] is None:
        bot.answer_callback_query(call.id, "Ошибка! Нажмите /start заново")
        return
        
    service_key = call.data.split("_")[1]
    if service_key not in PRICES:
        bot.answer_callback_query(call.id, "Старая кнопка! Нажмите /start")
        return
        
    user_orders[chat_id]["main_service"] = service_key
    show_addons_menu(call.message, chat_id)

def show_addons_menu(message, chat_id, message_id=None):
    order = user_orders[chat_id]
    type_idx = order["type_idx"]
    main_service = PRICES[order["main_service"]]
    
    total = main_service["costs"][type_idx]
    text_addons = ""
    
    for addon_key in order["addons"]:
        total += ADDONS[addon_key]["price"]
        text_addons += f"\n ➕ {ADDONS[addon_key]['name']} (+{ADDONS[addon_key]['price']}₽)"
        
    types_names = ["Легковая", "Кроссовер", "Минивэн/Микроавтобус"]
    text = (f"📋 *Текущий чек:*\n"
            f"• Авто: {types_names[type_idx]}\n"
            f"• База: {main_service['name']} ({main_service['costs'][type_idx]}₽)"
            f"{text_addons}\n\n"
            f"💰 *Итого к оплате: {total}₽*")
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for key, item in ADDONS.items():
        status = "✅ " if key in order["addons"] else ""
        buttons.append(types.InlineKeyboardButton(f"{status}{item['name']} ({item['price']}₽)", callback_data=f"a_{key}"))
        
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("🏁 ГОТОВО / СБРОС", callback_data="finish"))
    
    target_msg_id = message_id if message_id else message.id
    bot.edit_message_text(text, chat_id, target_msg_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("a_"))
def handle_addons(call):
    chat_id = call.message.chat.id
    if chat_id not in user_orders or user_orders[chat_id]["main_service"] is None:
        bot.answer_callback_query(call.id, "Ошибка! Нажмите /start")
        return
        
    addon_key = call.data.split("a_")[1]
    if addon_key in user_orders[chat_id]["addons"]:
        user_orders[chat_id]["addons"].remove(addon_key)
    else:
        user_orders[chat_id]["addons"].append(addon_key)
        
    show_addons_menu(call.message, chat_id, call.message.id)

@bot.callback_query_handler(func=lambda call: call.data == "finish")
def handle_finish(call):
    bot.answer_callback_query(call.id, "Чек закрыт!")
    send_welcome(call.message)

if __name__ == "__main__":
    bot.infinity_polling()
