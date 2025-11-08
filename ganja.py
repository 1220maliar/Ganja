import json
import os
import random
import glob
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройки
BOT_TOKEN = "8490323949:AAEJgbMBWTTaYzPJo8ztD7_1LDoWnPWX_CQ"
DATA_FILE = "game_data.json"
JACKPOT_PHOTOS_DIR = "jackpot_photos"  # Папка с фото для джекпотов

# Эмоджи для игр
EMOJIS = {
    "футбол": "⚽",
    "баскетбол": "🏀", 
    "дартс": "🎯",
    "слоты": "🎰"
}

# ================== СИСТЕМА ФОТО ДЛЯ ДЖЕКПОТОВ ==================

def create_jackpot_photos_dir():
    """Создает папку для фото джекпотов если её нет"""
    if not os.path.exists(JACKPOT_PHOTOS_DIR):
        os.makedirs(JACKPOT_PHOTOS_DIR)
        print(f"📁 Создана папка для фото джекпотов: {JACKPOT_PHOTOS_DIR}")
        print("📸 Закинь туда несколько фото для джекпотов!")

def get_random_jackpot_photo():
    """Возвращает путь к случайной фотке из папки джекпотов"""
    # Ищем все файлы картинок в папке
    photo_patterns = [
        f"{JACKPOT_PHOTOS_DIR}/*.jpg",
        f"{JACKPOT_PHOTOS_DIR}/*.jpeg", 
        f"{JACKPOT_PHOTOS_DIR}/*.png",
        f"{JACKPOT_PHOTOS_DIR}/*.gif"
    ]
    
    all_photos = []
    for pattern in photo_patterns:
        all_photos.extend(glob.glob(pattern))
    
    if all_photos:
        selected_photo = random.choice(all_photos)
        print(f"🎲 Выбрано случайное фото: {os.path.basename(selected_photo)}")
        return selected_photo
    else:
        print("❌ В папке jackpot_photos нет фото!")
        return None

# ================== СИСТЕМА ХРАНЕНИЯ ДАННЫХ ==================

def load_data():
    """Загружаем данные игроков"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    """Сохраняем данные игроков"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user_data(user_id):
    """Получаем данные пользователя"""
    data = load_data()
    user_id_str = str(user_id)
    if user_id_str not in data:
        data[user_id_str] = {
            "name": "",
            "ganja": 100,
            "games_played": 0,
            "games_won": 0,
            "current_bet": 10,
            "jackpots_won": 0
        }
        save_data(data)
    return data[user_id_str]

def update_user_data(user_id, new_data):
    """Обновляем данные пользователя"""
    data = load_data()
    user_id_str = str(user_id)
    
    if user_id_str not in data:
        data[user_id_str] = {
            "name": "",
            "ganja": 100,
            "games_played": 0,
            "games_won": 0,
            "current_bet": 10,
            "jackpots_won": 0
        }
    
    data[user_id_str].update(new_data)
    save_data(data)

def add_ganja(user_id, amount):
    """Добавляем ганжу пользователю"""
    user_data = get_user_data(user_id)
    user_data["ganja"] += amount
    update_user_data(user_id, {"ganja": user_data["ganja"]})
    return user_data["ganja"]

# ================== ИГРОВАЯ ЛОГИКА ==================

def play_football():
    """Игра в футбол - 40% шанс выигрыша"""
    return random.random() < 0.25

def play_basketball():
    """Игра в баскетбол - 35% шанс выигрыша"""
    return random.random() < 0.20

def play_darts():
    """Игра в дартс - 50% шанс выигрыша"""
    return random.random() < 0.25

def play_slots():
    """Игровые автоматы с джекпотом"""
    rand = random.random()
    if rand < 0.09:  # 2% шанс на джекпот
        return "jackpot"
    elif rand < 0.18:  # 25% шанс на обычный выигрыш
        return "win"
    else:
        return "lose"

def calculate_win_amount(game_type, bet_amount, result="win"):
    """Рассчитываем выигрыш"""
    multipliers = {
        "футбол": 3,
        "баскетбол": 4, 
        "дартс": 2,
        "слоты": 10
    }
    
    if result == "jackpot":
        return bet_amount * 50
    elif result == "win":
        return bet_amount * multipliers.get(game_type, 1)
    else:
        return 0
    # ================== КЛАВИАТУРЫ ==================

def get_main_keyboard():
    """Основная клавиатура"""
    keyboard = [
        [KeyboardButton("⚽ Футбол"), KeyboardButton("🏀 Баскетбол")],
        [KeyboardButton("🎯 Дартс"), KeyboardButton("🎰 Слоты")],
        [KeyboardButton("💰 Моя ганжа"), KeyboardButton("📊 Статистика")],
        [KeyboardButton("🎲 Выбрать ставку"), KeyboardButton("🎁 Получить ганжу")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_bet_keyboard():
    """Клавиатура выбора ставки"""
    keyboard = [
        [KeyboardButton("🎲 10 ганжи"), KeyboardButton("🎲 25 ганжи")],
        [KeyboardButton("🎲 50 ганжи"), KeyboardButton("🎲 100 ганжи")],
        [KeyboardButton("⬅️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_shop_keyboard():
    """Клавиатура магазина"""
    keyboard = [
        [KeyboardButton("🎁 100 ганжи"), KeyboardButton("🎁 200 ганжи")],
        [KeyboardButton("🎁 500 ганжи"), KeyboardButton("🎁 1000 ганжи")],
        [KeyboardButton("⬅️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ================== СИСТЕМА СТАВОК ==================

def get_user_bet(user_id):
    """Получаем текущую ставку пользователя"""
    user_data = get_user_data(user_id)
    return user_data.get("current_bet", 10)

def set_user_bet(user_id, bet_amount):
    """Устанавливаем ставку пользователя"""
    update_user_data(user_id, {"current_bet": bet_amount})
    return bet_amount

# ================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==================

async def show_balance(update: Update, user_data):
    """Показать баланс ганжи"""
    current_bet = get_user_bet(update.message.from_user.id)
    balance_text = f"""
💰 Твой баланс:

Ганжа: {user_data['ganja']} 💰
Текущая ставка: {current_bet} ганжи
Игр сыграно: {user_data['games_played']}
Побед: {user_data['games_won']}
Джекпотов: {user_data.get('jackpots_won', 0)} 🎰
    """
    await update.message.reply_text(balance_text)

async def show_stats(update: Update, user_data):
    """Показать статистику"""
    games_played = user_data["games_played"]
    games_won = user_data["games_won"]
    jackpots_won = user_data.get("jackpots_won", 0)
    win_rate = (games_won / games_played * 100) if games_played > 0 else 0
    
    stats_text = f"""
📊 Твоя статистика:

🎮 Игр сыграно: {games_played}
🏆 Побед: {games_won}
🎰 Джекпотов: {jackpots_won}
📈 Процент побед: {win_rate:.1f}%
💰 Ганжа: {user_data['ganja']}

Продолжай в том же духе! 💪
    """
    await update.message.reply_text(stats_text)

# ================== КОМАНДЫ БОТА ==================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.message.from_user
    user_id = user.id
    
    # Инициализируем пользователя
    user_data = get_user_data(user_id)
    if not user_data["name"]:
        update_user_data(user_id, {"name": user.first_name, "current_bet": 10})
    
    current_bet = get_user_bet(user_id)
    
    welcome_text = f"""
🎮 Добро пожаловать в Игровой Бот, {user.first_name}!

Ты получил стартовые 100 единиц ганжи! 💰

Твоя текущая ставка: {current_bet} ганжи

Доступные игры:
⚽ Футбол - выигрыш x3
🏀 Баскетбол - выигрыш x4  
🎯 Дартс - выигрыш x2
🎰 Слоты - выигрыш x10 + ШАНС НА ДЖЕКПОТ! 🎉

🎲 Можно изменить ставку - 10, 25, 50 или 100 ганжи
🎁 Можно получить ганжу бесплатно

Выбирай игру и удачи! 🍀
    """
    
    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
🎮 Правила игр:

Можно менять ставку: 10, 25, 50, 100 ганжи

⚽ Футбол - 40% шанс выигрыша (x3)
🏀 Баскетбол - 35% шанс выигрыша (x4)  
🎯 Дартс - 50% шанс выигрыша (x2)
🎰 Слоты - 25% шанс выигрыша (x10) + 2% шанс на ДЖЕКПОТ (x50)! 🎉

💰 Моя ганжа - посмотреть баланс
📊 Статистика - твоя игровая статистика
🎲 Выбрать ставку - изменить размер ставки
🎁 Получить ганжу - бесплатно получить ганжу
Удачи в играх! 🍀
    """
    await update.message.reply_text(help_text)

# ================== ОБРАБОТЧИКИ ИГР И МАГАЗИНА ==================

async def handle_game_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора игры и магазина"""
    user_text = update.message.text
    user = update.message.from_user
    user_id = user.id
    user_data = get_user_data(user_id)
    
    # Получаем текущую ставку пользователя
    current_bet = get_user_bet(user_id)
    
    # Если пользователь выбирает ставку
    if user_text.startswith("🎲 Выбрать ставку"):
        await update.message.reply_text(
            f"💰 Твоя текущая ставка: {current_bet} ганжи\n\n"
            "Выбери новую ставку:",
            reply_markup=get_bet_keyboard()
        )
        return
    
    # Если пользователь заходит в магазин
    if user_text == "🎁 Получить ганжу":
        await update.message.reply_text(
            f"🎁 **Бесплатная ганжа**\n\n"
            f"Твоя ганжа: {user_data['ganja']} 💰\n\n"
            "Выбери сколько ганжи получить:",
            reply_markup=get_shop_keyboard()
        )
        return
    
    # Обработка выбора ставки
    bet_actions = {
        "🎲 10 ганжи": 10,
        "🎲 25 ганжи": 25, 
        "🎲 50 ганжи": 50,
        "🎲 100 ганжи": 100
    }
    
    if user_text in bet_actions:
        new_bet = bet_actions[user_text]
        set_user_bet(user_id, new_bet)
        await update.message.reply_text(
            f"✅ Ставка установлена: {new_bet} ганжи",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Обработка бесплатной ганжи
    free_ganja_actions = {
        "🎁 100 ганжи": 100,
        "🎁 200 ганжи": 200,
        "🎁 500 ганжи": 500,
        "🎁 1000 ганжи": 1000
    }
    
    if user_text in free_ganja_actions:
        ganja_amount = free_ganja_actions[user_text]
        new_balance = add_ganja(user_id, ganja_amount)
        
        await update.message.reply_text(
            f"🎉 **Получено {ganja_amount} ганжи!**\n\n"
            f"💰 Новый баланс: {new_balance} ганжи\n\n"
            f"Удачи в играх! 🎮",
            reply_markup=get_main_keyboard()
        )
        return
    
    if user_text == "⬅️ Назад":
        await update.message.reply_text(
            "Возвращаемся в главное меню:",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Проверяем достаточно ли ганжи для текущей ставки
    if user_data["ganja"] < current_bet:
        await update.message.reply_text(
            f"❌ Недостаточно ганжи! Нужно {current_bet}, а у тебя {user_data['ganja']}\n"
            f"Текущая ставка: {current_bet} ганжи\n\n"
            "Зайди в магазин и получи бесплатную ганжу! 🎁",
            reply_markup=get_main_keyboard()
        )
        return
    
    games = {
        "⚽ футбол": ("футбол", play_football),
        "🏀 баскетбол": ("баскетбол", play_basketball), 
        "🎯 дартс": ("дартс", play_darts),
        "🎰 слоты": ("слоты", play_slots)
    }
    
    # Убираем эмодзи для поиска
    game_key = user_text.lower()
    for emoji_game, (game_type, game_func) in games.items():
        if game_type in game_key:
            # Снимаем ставку
            new_balance = add_ganja(user_id, -current_bet)
            
            # Играем!
            result = game_func()
            
            # Для слотов отдельная логика с фото джекпота
            if game_type == "слоты":
                if result == "jackpot":
                    win_amount = calculate_win_amount(game_type, current_bet, "jackpot")
                    new_balance = add_ganja(user_id, win_amount)
                    user_data["games_won"] += 1
                    user_data["jackpots_won"] = user_data.get("jackpots_won", 0) + 1
                    
                    # Пытаемся отправить случайное фото
                    photo_path = get_random_jackpot_photo()
                    photo_sent = False
                    
                    if photo_path and os.path.exists(photo_path):
                        try:
                            with open(photo_path, 'rb') as photo:
                                await update.message.reply_photo(
                                    photo,
                                    caption="🎰 🎉 ДЖЕКПОТ! 🎉 🎰\n\nТы сорвал куш! 💎"
                                )
                            photo_sent = True
                            print(f"✅ Отправлено фото джекпота: {os.path.basename(photo_path)}")
                        except Exception as e:
                            print(f"❌ Ошибка отправки фото: {e}")
                            photo_sent = False
                    
                    result_text = f"""
🎰 💎 ДЖЕКПОТ! 💎 🎰

Ты сорвал куш! 🏆
Ставка: {current_bet} ганжи
ВЫИГРЫШ: +{win_amount} ганжи 💰
Твой баланс: {new_balance} ганжи

🎊 ПОЗДРАВЛЯЕМ С ДЖЕКПОТОМ! 🎊
                    """
                    
                    # Если фото не отправилось, отправляем только текст
                    if not photo_sent:
                        await update.message.reply_text(result_text)
                    
                elif result == "win":
                    win_amount = calculate_win_amount(game_type, current_bet)
                    new_balance = add_ganja(user_id, win_amount)
                    user_data["games_won"] += 1
                    
                    result_text = f"""
🎰 🎉 ПОБЕДА! Ты выиграл! 🎉 🎰

Игра: Слоты
Ставка: {current_bet} ганжи
Выигрыш: +{win_amount} ганжи 💰
Твой баланс: {new_balance} ганжи

Поздравляю! 🏆
                    """
                    await update.message.reply_text(result_text)
                else:
                    result_text = f"""
🎰 💔 Проигрыш... 🎰

Игра: Слоты
Ставка: {current_bet} ганжи
Проиграно: {current_bet} ганжи
Твой баланс: {new_balance} ганжи

Попробуй еще раз! 🍀
                    """
                    await update.message.reply_text(result_text)
            else:
                # Для других игр
                is_win = result
                win_amount = calculate_win_amount(game_type, current_bet) if is_win else 0
                
                if is_win:
                    user_data["games_won"] += 1
                    new_balance = add_ganja(user_id, win_amount)
                
                game_emoji = EMOJIS.get(game_type, "🎮")
                
                if is_win:
                    result_text = f"""
{game_emoji} 🎉 ПОБЕДА! Ты выиграл! 🎉 {game_emoji}

Игра: {game_type.title()}
Ставка: {current_bet} ганжи
Выигрыш: +{win_amount} ганжи 💰
Твой баланс: {new_balance} ганжи

Поздравляю! 🏆
                    """
                else:
                    result_text = f"""
{game_emoji} 💔 Проигрыш... {game_emoji}

Игра: {game_type.title()}
Ставка: {current_bet} ганжи
Проиграно: {current_bet} ганжи
Твой баланс: {new_balance} ганжи

Попробуй еще раз! 🍀
                    """
                
                await update.message.reply_text(result_text)
            
            # Обновляем статистику
            user_data["games_played"] += 1
            update_user_data(user_id, {
                "games_played": user_data["games_played"],
                "games_won": user_data["games_won"],
                "jackpots_won": user_data.get("jackpots_won", 0)
            })
            return
    
    # Если это не игра, обрабатываем другие кнопки
    if user_text == "💰 Моя ганжа":
        await show_balance(update, user_data)
    elif user_text == "📊 Статистика":
        await show_stats(update, user_data)
    else:
        await update.message.reply_text("Выбери игру из меню! 🎮", reply_markup=get_main_keyboard())

# ================== ЗАПУСК БОТА ==================

def main():
    """Запуск бота"""
    # Создаем папку для фото джекпотов
    create_jackpot_photos_dir()
    
    # Проверяем есть ли фото
    photo_count = len(glob.glob(f"{JACKPOT_PHOTOS_DIR}/*.jpg")) + \
                  len(glob.glob(f"{JACKPOT_PHOTOS_DIR}/*.jpeg")) + \
                  len(glob.glob(f"{JACKPOT_PHOTOS_DIR}/*.png")) + \
                  len(glob.glob(f"{JACKPOT_PHOTOS_DIR}/*.gif"))
    print(f"📸 Найдено фото для джекпотов: {photo_count}")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики команд
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("rules", help_command))
    
    # Обработчики сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_game_selection))
    
    print("🎮 Игровой бот запущен!")
    print("💰 Система ганжи активирована")
    print("🎁 Бесплатная ганжа доступна")
    print("🎰 Джекпот в слотах: 2% шанс")
    print("📸 Случайные фото при джекпоте: ВКЛ")
    print("💾 Данные сохраняются в:", DATA_FILE)
    app.run_polling()
    
    while True:
        try:
            print("🔄 Запускаем бота...")
            app = Application.builder().token(BOT_TOKEN).build()
            
            # Обработчики команд
            app.add_handler(CommandHandler("start", start_command))
            app.add_handler(CommandHandler("help", help_command))
            app.add_handler(CommandHandler("rules", help_command))
            
            # Обработчики сообщений
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_game_selection))
            
            print("🎮 Игровой бот запущен!")
            print("💰 Система ганжи активирована")
            print("🎰 Джекпот в слотах: 2% шанс")
            print("📸 Случайные фото при джекпоте: ВКЛ")
            
            # Запускаем бота
            app.run_polling()
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print("🔄 Перезапуск через 10 секунд...")
            import time
            time.sleep(10)

if __name__ == "__main__":
    main()