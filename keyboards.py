from telebot import types

def create_lang_keyboard():
    """Клавиатура для выбора языка"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)

    buttons = [
        '🇬🇧 Английский', '🇩🇪 Немецкий', '🇫🇷 Французский',
        '🇪🇸 Испанский', '🇮🇹 Итальянский', '🇷🇺 Русский',
        '🇺🇦 Украинский', '🇵🇱 Польский', '🔙 Назад'
    ]

    # Создаем ряды по 3 кнопки
    for i in range(0, len(buttons), 3):
        row = buttons[i:i+3]
        markup.row(*[types.KeyboardButton(btn) for btn in row])

    return markup

def create_main_keyboard():
    """Основная клавиатура для главного меню"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    buttons = [
        '🌍 Выбрать язык', '📝 Переводчик',
        '📜 Моя история', '📊 Моя статистика',
        '🆘 Помощь'
    ]

    for i in range(0, len(buttons), 2):
        row = buttons[i:i+2]
        markup.row(*[types.KeyboardButton(btn) for btn in row])

    return markup

def create_admin_main_keyboard():
    """Главная клавиатура админ-панели"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    buttons = [
        '📈 Общая статистика', '👥 Управление пользователями',
        '📜 Просмотр переводов', '🌍 Популярные языки',
        '👑 Управление админами', '📤 Экспорт данных',
        '🔄 Очистка данных', '🔙 В главное меню'
    ]

    for i in range(0, len(buttons), 2):
        row = buttons[i:i+2]
        markup.row(*[types.KeyboardButton(btn) for btn in row])

    return markup

def create_admin_users_keyboard():
    """Клавиатура для управления пользователями"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    buttons = [
        '📋 Список пользователей', '👤 Инфо о пользователе',
        '📊 Переводы пользователя', '🔙 В админ-панель'
    ]

    for i in range(0, len(buttons), 2):
        row = buttons[i:i+2]
        markup.row(*[types.KeyboardButton(btn) for btn in row])

    return markup

def create_admin_translations_keyboard():
    """Клавиатура для просмотра переводов"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    buttons = [
        '📜 Последние переводы', '🔍 Поиск по пользователю',
        '📅 Переводы за сегодня', '🔙 В админ-панель'
    ]

    for i in range(0, len(buttons), 2):
        row = buttons[i:i+2]
        markup.row(*[types.KeyboardButton(btn) for btn in row])

    return markup

def create_admin_management_keyboard():
    """Клавиатура для управления администраторами"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    buttons = [
        '➕ Добавить админа', '➖ Удалить админа',
        '📋 Список админов', '🔙 В админ-панель'
    ]

    for i in range(0, len(buttons), 2):
        row = buttons[i:i+2]
        markup.row(*[types.KeyboardButton(btn) for btn in row])

    return markup

def create_admin_export_keyboard():
    """Клавиатура для экспорта данных"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    buttons = [
        '📊 Экспорт в JSON', '📈 Экспорт в CSV',
        '🔙 В админ-панель'
    ]

    for i in range(0, len(buttons), 2):
        row = buttons[i:i+2]
        markup.row(*[types.KeyboardButton(btn) for btn in row])

    return markup

def create_admin_cleanup_keyboard():
    """Клавиатура для очистки данных"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    buttons = [
        '🗑️ Очистить всю историю', '📅 Очистить старые данные',
        '🔙 В админ-панель'
    ]

    for i in range(0, len(buttons), 2):
        row = buttons[i:i+2]
        markup.row(*[types.KeyboardButton(btn) for btn in row])

    return markup

def create_back_keyboard():
    """Простая клавиатура с кнопкой назад"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🔙 Назад'))
    return markup

def create_cleanup_options_keyboard():
    """Клавиатура для выбора периода очистки"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)

    buttons = [
        '1 день', '7 дней', '30 дней',
        '90 дней', '🔙 Назад'
    ]

    for i in range(0, len(buttons), 3):
        row = buttons[i:i+3]
        markup.row(*[types.KeyboardButton(btn) for btn in row])

    return markup