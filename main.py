import telebot
from telebot import types

# Твой токен, который ты скинул
TOKEN = '8693012719:AAFFRW4JMaQVmXPIIgkcVLJC-Wwe43Y4vDE'
bot = telebot.TeleBot(TOKEN)

# Данные из твоего прайса
PRICES = {
    "express": {"name": "⚡ Экспресс-мойка", "costs": [500, 600, 700]},
    "body": {"name": "🚗 Мойка кузова", "costs": [600, 800, 1000]},
    "two_phase": {"name": "🧼 Двух-фазная кузова", "costs": [1100, 1400, 1700]},
    "three_phase": {"name": "✨ Трёх-фазная кузова", "costs": [1400, 1700, 2000]},
    "mats": {"name": "🧺 Кузов + коврики", "costs": [700, 1000, 1300]},
    "salon": {"name": "🧽 Кузов + салон", "costs": [1500, 2000, 2500]},
    "hard_wax": {"name": "🕯️ Твердый воск", "costs": [1500, 2000, 2500]},
}

ADDONS = {
    "wax": {"name": "Обработка воском", "price": 300},
    "quartz": {"name": "Обработка кварцем", "price": 600},
    "bitumen": {"name": "Очистка битума (1 дет.)", "price": 200},
    "engine": {"name": "Мойка двигателя", "price": 1500},
    "plastic": {"name": "Полироль пластика", "price": 500},
    "leather": {"name": "Кондиционер кожи", "price": 500},
    "tires": {"name": "Чернение резины", "price": 300},
    "trunk": {"name": "Уборка багажника", "price": 500},
}

# Временное хранение заказов пользователей
user_orders = {}

@bot.message_handler(commands=['start', 'reset'])
def send_welcome(message):
    user_orders[message.chat.id] = {"type_idx": None, "main_service": None, "addons": []}
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🚗 Легковая", callback_data="type_0"),
        types.InlineKeyboardButton("🚙 Кроссовер / Паркетник", callback_data="type_1"),
        types.InlineKeyboardButton("🚐 Минивэн / Микроавтобус", callback_data="type_2")
    )
    bot.send_message(message.chat.id, "👋 Привет! Выбери тип автомобиля для расчета:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("type_"))
def handle_type(call):
    type_idx = int(call.data.split("_")[1])
    user_orders[call.message.chat.id]["type_idx"] = type_idx
    
    types_names = ["Легковая", "Кроссовер", "Минивэн/Микроавтобус"]
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, item in PRICES.items():
        price = item["costs"][type_idx]
        markup.add(types.InlineKeyboardButton(f"{item['name']} — {price}₽", callback_data=f"main_{key}"))
        
    bot.edit_message_text(f"Выбран тип: *{types_names[type_idx]}*\nТеперь выбери основную услугу:", 
                          call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("main_"))
def handle_main_service(call):
    service_key = call.data.split("_")[1]
    user_orders[call.message.chat.id]["main_service"] = service_key
    
    show_addons_menu(call.message, call.message.chat.id)

def show_addons_menu(message, chat_id, message_id=None):
    order = user_orders[chat_id]
    type_idx = order["type_idx"]
    main_service = PRICES[order["main_service"]]
    
    # Считаем текущую сумму
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
    
    # Кнопки допов
    buttons = []
    for key, item in ADDONS.items():
        status = "✅ " if key in order["addons"] else ""
        buttons.append(types.InlineKeyboardButton(f"{status}{item['name']} ({item['price']}₽)", callback_data=f"addon_{key}"))
        
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("🏁 ГОТОВО / СБРОС", callback_data="finish"))
    
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
    else:
        bot.edit_message_text(text, chat_id, message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("addon_"))
def handle_addons(call):
    addon_key = call.data.split("_")[1]
    chat_id = call.message.chat.id
    
    if addon_key in user_orders[chat_id]["addons"]:
        user_orders[chat_id]["addons"].remove(addon_key)
    else:
        user_orders[chat_id]["addons"].append(addon_key)
        
    show_addons_menu(call.message, chat_id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "finish")
def handle_finish(call):
    bot.answer_callback_query(call.id, "Чек закрыт!")
    send_welcome(call.message)

if __name__ == "__main__":
    print("Бот запущен и ждет клиентов...")
    bot.infinity_polling()
