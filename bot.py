from config import BOT_TOKEN
from keyboards import (create_lang_keyboard, create_main_keyboard,
                       create_admin_main_keyboard, create_admin_users_keyboard,
                       create_admin_translations_keyboard, create_admin_management_keyboard,
                       create_admin_export_keyboard, create_admin_cleanup_keyboard,
                       create_back_keyboard, create_cleanup_options_keyboard)
from database import db
from telebot import TeleBot
from telebot.types import ReplyKeyboardRemove
import requests
import json
import time
import sys
import os
from datetime import datetime, timedelta
from io import StringIO

if not os.path.exists('temp'):
    os.makedirs('temp')

bot = TeleBot(BOT_TOKEN)

# Словарь для хранения состояний пользователей
user_states = {}


def simple_translate(text, target_lang='en'):
    """Простой переводчик через Google Translate API"""
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            'client': 'gtx',
            'sl': 'auto',
            'tl': target_lang,
            'dt': 't',
            'q': text
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            translated_text = ''
            for item in data[0]:
                if item[0]:
                    translated_text += item[0]
            return translated_text
        return "Ошибка перевода: сервер не ответил"
    except Exception as e:
        return f"Ошибка перевода: {str(e)}"


def get_lang_name(lang_code):
    """Получить название языка по коду"""
    lang_names = {
        'en': '🇬🇧 Английский',
        'de': '🇩🇪 Немецкий',
        'fr': '🇫🇷 Французский',
        'es': '🇪🇸 Испанский',
        'it': '🇮🇹 Итальянский',
        'ru': '🇷🇺 Русский',
        'uk': '🇺🇦 Украинский',
        'pl': '🇵🇱 Польский'
    }
    return lang_names.get(lang_code, lang_code.upper())


# ==================== ОСНОВНЫЕ КОМАНДЫ ====================

@bot.message_handler(commands=['start'])
def start_message(message):
    """Обработчик команды start"""
    user_id = message.from_user.id
    username = message.from_user.username or "Не указан"
    first_name = message.from_user.first_name or "Пользователь"
    last_name = message.from_user.last_name or ""

    # Добавляем пользователя в базу
    db.add_user(user_id, username, first_name, last_name)

    welcome_text = (
        "🤖 *Добро пожаловать в Translation G.X!*\n\n"
        "✨ *Возможности бота:*\n"
        "• 🌍 Перевод на 100+ языков\n"
        "• ⚡ Мгновенный перевод\n"
        "• 📊 История и статистика\n"
        "• 💫 Умный интерфейс\n\n"
        "🚀 *Быстрый старт:*\n"
        "1. Нажмите '🌍 Выбрать язык'\n"
        "2. Отправьте текст для перевода\n"
        "3. Наслаждайтесь результатом!"
    )

    # Проверяем админа - только для вас показываем админ-панель
    if db.is_admin(user_id):
        welcome_text += "\n\n👑 *Доступна админ-панель:* /admin"

    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown',
                     reply_markup=create_main_keyboard())


@bot.message_handler(commands=['myid'])
def my_id_command(message):
    """Показать мой user_id - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    try:
        user_id = message.from_user.id
        first_name = message.from_user.first_name or "Не указано"
        username = message.from_user.username or "нет"

        text = (
            f"👤 *Ваш профиль*\n\n"
            f"🆔 *User ID:* `{user_id}`\n"
            f"📛 *Имя:* {first_name}\n"
            f"🔗 *Username:* @{username}\n"
            f"👑 *Статус:* {'Администратор 👑' if db.is_admin(user_id) else 'Пользователь'}\n\n"
            f"💡 *Совет:* Сохраните ваш User ID"
        )

        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    except Exception as e:
        print(f"Ошибка в myid: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при получении информации")


@bot.message_handler(commands=['language'])
def language_command(message):
    """Обработчик команды language"""
    keyboard = create_lang_keyboard()
    bot.send_message(
        message.chat.id,
        '🌍 *Выберите язык для перевода:*',
        parse_mode='Markdown',
        reply_markup=keyboard
    )


@bot.message_handler(commands=['help'])
def help_command(message):
    """Обработчик команды help"""
    user_id = message.from_user.id

    help_text = (
        "🆘 *Центр помощи*\n\n"
        "📋 *Основные команды:*\n"
        "• /start - Главное меню\n"
        "• /language - Выбор языка\n"
        "• /myid - Мой профиль\n"
        "• /stats - Моя статистика\n"
        "• /history - История переводов\n"
        "• /help - Помощь\n\n"

        "🛠 *Функции:*\n"
        "• Автоопределение языка\n"
        "• История переводов\n"
        "• Статистика использования\n"
        "• Быстрые кнопки\n\n"

        "💡 *Совет:* Используйте кнопки для быстрого доступа!"
    )

    # Только администраторам показываем команду админ-панели
    if db.is_admin(user_id):
        help_text += "\n\n👑 *Админ-команды:*\n/admin - Админ-панель"

    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')


@bot.message_handler(commands=['stats'])
def stats_command(message):
    """Показать статистику пользователя"""
    user_id = message.from_user.id
    stats = db.get_user_stats(user_id)

    stats_text = (
        f"📊 *Ваша статистика*\n\n"
        f"📈 *Переводов выполнено:* {stats['translation_count']}\n"
        f"🌍 *Языков использовано:* {stats['languages_count']}\n"
        f"⏰ *Последний перевод:* {stats['last_translation']}\n\n"
        f"🎯 *Цель:* 100 переводов!"
    )

    bot.send_message(message.chat.id, stats_text, parse_mode='Markdown')


@bot.message_handler(commands=['history'])
def history_command(message):
    """Показать историю переводов"""
    user_id = message.from_user.id
    history = db.get_user_history(user_id, limit=5)

    if not history:
        bot.send_message(message.chat.id,
                         "📭 *История переводов пуста*\n\n"
                         "Сделайте первый перевод и он появится здесь!",
                         parse_mode='Markdown')
        return

    history_text = "📜 *Последние 5 переводов:*\n\n"
    for i, item in enumerate(history, 1):
        lang_from = item.get('source_lang', 'auto').upper()
        lang_to = get_lang_name(item.get('target_lang', 'en'))
        time_str = item.get('timestamp', '')[:16] if item.get('timestamp') else "Неизвестно"

        history_text += (
            f"{i}. _{time_str}_\n"
            f"   {lang_from} → {lang_to}\n"
            f"   📝 {item.get('original_text', '')[:40]}...\n\n"
        )

    bot.send_message(message.chat.id, history_text, parse_mode='Markdown')


# ==================== ИСПРАВЛЕННАЯ АДМИН-ПАНЕЛЬ ====================

@bot.message_handler(commands=['admin'])
def admin_command(message):
    """Админ-панель - ТОЛЬКО для администраторов"""
    user_id = message.from_user.id

    if not db.is_admin(user_id):
        bot.send_message(message.chat.id,
                         "❌ Команда не найдена!\n\n"
                         "Используйте /help для списка доступных команд.")
        return

    # Очищаем состояния при входе в админку
    if user_id in user_states:
        del user_states[user_id]

    admin_text = (
        "👑 Админ-панель\n\n"
        "💼 Центр управления ботом\n\n"
        "📊 Выберите раздел для управления:"
    )

    bot.send_message(message.chat.id, admin_text,
                     reply_markup=create_admin_main_keyboard())


# Обработчики главного меню админ-панели
@bot.message_handler(func=lambda message: message.text in [
    '📈 Общая статистика', '👥 Управление пользователями', '📜 Просмотр переводов',
    '🌍 Популярные языки', '👑 Управление админами', '📤 Экспорт данных',
    '🔄 Очистка данных', '🔙 В главное меню'
])
def handle_admin_main_buttons(message):
    user_id = message.from_user.id

    if not db.is_admin(user_id):
        return

    # Очищаем состояние при смене раздела
    if user_id in user_states:
        del user_states[user_id]

    if message.text == '📈 Общая статистика':
        stats = db.get_global_stats()

        stats_text = (
            "📈 Общая статистика бота\n\n"
            f"👥 Пользователи: {stats['users_count']}\n"
            f"👑 Админы: {stats['admins_count']}\n"
            f"📝 Всего переводов: {stats['translations_count']}\n"
            f"🔥 Активных сегодня: {stats['active_today']}\n"
            f"📅 Активных за неделю: {stats['active_week']}\n"
            f"🏆 Самый активный: {stats.get('top_user', 'Нет данных')}\n\n"
            f"⏰ Статистика на: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )

        bot.send_message(message.chat.id, stats_text)

    elif message.text == '👥 Управление пользователями':
        users_text = (
            "👥 Управление пользователями\n\n"
            "📊 Функции управления пользователями\n\n"
            "Выберите действие:"
        )
        bot.send_message(message.chat.id, users_text,
                         reply_markup=create_admin_users_keyboard())

    elif message.text == '📜 Просмотр переводов':
        translations_text = (
            "📜 Просмотр переводов\n\n"
            "🔍 Просмотр истории переводов\n\n"
            "Выберите действие:"
        )
        bot.send_message(message.chat.id, translations_text,
                         reply_markup=create_admin_translations_keyboard())

    elif message.text == '🌍 Популярные языки':
        languages = db.get_top_languages()

        if not languages:
            bot.send_message(message.chat.id, "❌ Нет данных о языках.")
            return

        languages_text = "🌍 Топ популярных языков:\n\n"
        total_translations = sum(lang['count'] for lang in languages)

        for i, lang in enumerate(languages, 1):
            lang_name = get_lang_name(lang['target_lang'])
            percentage = (lang['count'] / total_translations) * 100 if total_translations > 0 else 0
            languages_text += f"{i}. {lang_name} - {lang['count']} ({percentage:.1f}%)\n"

        languages_text += f"\n📊 Всего переводов: {total_translations}"

        bot.send_message(message.chat.id, languages_text)

    elif message.text == '👑 Управление админами':
        admin_management_text = (
            "👑 Управление администраторами\n\n"
            "⚡ Быстрое управление правами\n\n"
            "Выберите действие:"
        )
        bot.send_message(message.chat.id, admin_management_text,
                         reply_markup=create_admin_management_keyboard())

    elif message.text == '📤 Экспорт данных':
        export_text = (
            "📤 Экспорт данных\n\n"
            "💾 Экспорт данных в различные форматы\n\n"
            "Выберите формат экспорта:"
        )
        bot.send_message(message.chat.id, export_text,
                         reply_markup=create_admin_export_keyboard())

    elif message.text == '🔄 Очистка данных':
        cleanup_text = (
            "🔄 Очистка данных\n\n"
            "⚠️ Осторожно! Это действие необратимо\n\n"
            "Выберите тип очистки:"
        )
        bot.send_message(message.chat.id, cleanup_text,
                         reply_markup=create_admin_cleanup_keyboard())

    elif message.text == '🔙 В главное меню':
        start_message(message)


# Обработчики управления пользователями
@bot.message_handler(func=lambda message: message.text in [
    '📋 Список пользователей', '👤 Инфо о пользователе',
    '📊 Переводы пользователя', '🔙 В админ-панель'
])
def handle_admin_users_buttons(message):
    user_id = message.from_user.id

    if not db.is_admin(user_id):
        return

    # Очищаем состояние
    if user_id in user_states:
        del user_states[user_id]

    if message.text == '📋 Список пользователей':
        users = db.get_all_users()

        if not users:
            bot.send_message(message.chat.id, "❌ Нет пользователей.")
            return

        users_text = f"👥 Все пользователи ({len(users)}):\n\n"

        for i, user in enumerate(users[:15], 1):
            admin_flag = " 👑" if user.get('is_admin') else ""
            created_at = user.get('created_at', '')[:10] if user.get('created_at') else 'Неизвестно'
            users_text += (
                f"{i}. {user.get('first_name', 'No name')}{admin_flag}\n"
                f"   ID: {user['user_id']}\n"
                f"   Дата: {created_at}\n\n"
            )

        if len(users) > 15:
            users_text += f"... и еще {len(users) - 15} пользователей"

        bot.send_message(message.chat.id, users_text)

    elif message.text == '👤 Инфо о пользователе':
        user_states[user_id] = 'waiting_user_info'
        bot.send_message(message.chat.id,
                         "👤 Информация о пользователе\n\n"
                         "Отправьте user_id пользователя:",
                         reply_markup=create_back_keyboard())

    elif message.text == '📊 Переводы пользователя':
        user_states[user_id] = 'waiting_user_translations'
        bot.send_message(message.chat.id,
                         "📊 Переводы пользователя\n\n"
                         "Отправьте user_id пользователя:",
                         reply_markup=create_back_keyboard())

    elif message.text == '🔙 В админ-панель':
        admin_command(message)


# ИСПРАВЛЕННЫЕ ОБРАБОТЧИКИ ПРОСМОТРА ПЕРЕВОДОВ
@bot.message_handler(func=lambda message: message.text in [
    '📜 Последние переводы', '🔍 Поиск по пользователю',
    '📅 Переводы за сегодня', '🔙 В админ-панель'
])
def handle_admin_translations_buttons(message):
    user_id = message.from_user.id

    if not db.is_admin(user_id):
        return

    # Очищаем состояние
    if user_id in user_states:
        del user_states[user_id]

    if message.text == '📜 Последние переводы':
        translations = db.get_recent_translations(limit=10)

        if not translations:
            bot.send_message(message.chat.id, "❌ Нет переводов в истории.")
            return

        translations_text = "📜 Последние 10 переводов:\n\n"

        for i, trans in enumerate(translations, 1):
            user_name = trans.get('first_name', f"ID: {trans['user_id']}")
            lang_to = get_lang_name(trans.get('target_lang', 'en'))
            time_str = trans.get('timestamp', '')[:16] if trans.get('timestamp') else 'Неизвестно'

            translations_text += (
                f"{i}. 👤 {user_name}\n"
                f"   ⏰ {time_str}\n"
                f"   🌍 {trans.get('source_lang', 'auto')} → {lang_to}\n"
                f"   📝 {trans.get('original_text', '')[:50]}...\n\n"
            )

        bot.send_message(message.chat.id, translations_text)

    elif message.text == '🔍 Поиск по пользователю':
        user_states[user_id] = 'waiting_user_translations_search'
        bot.send_message(message.chat.id,
                         "🔍 Поиск переводов по пользователю\n\n"
                         "Отправьте user_id пользователя:",
                         reply_markup=create_back_keyboard())

    elif message.text == '📅 Переводы за сегодня':
        # Получаем переводы за сегодня
        today = datetime.now().strftime('%Y-%m-%d')
        translations = db.get_translations_by_date(today)

        if not translations:
            bot.send_message(message.chat.id,
                             f"📅 Нет переводов за сегодня ({today})")
            return

        translations_text = f"📅 Переводы за сегодня ({today}):\n\n"

        for i, trans in enumerate(translations[:10], 1):
            user_name = trans.get('first_name', f"ID: {trans['user_id']}")
            lang_to = get_lang_name(trans.get('target_lang', 'en'))
            time_str = trans.get('timestamp', '')[11:16] if trans.get('timestamp') else 'Неизвестно'

            translations_text += (
                f"{i}. 👤 {user_name}\n"
                f"   ⏰ {time_str}\n"
                f"   🌍 {trans.get('source_lang', 'auto')} → {lang_to}\n"
                f"   📝 {trans.get('original_text', '')[:40]}...\n\n"
            )

        if len(translations) > 10:
            translations_text += f"\n... и еще {len(translations) - 10} переводов"

        bot.send_message(message.chat.id, translations_text)

    elif message.text == '🔙 В админ-панель':
        admin_command(message)


# Обработчики управления администраторами
@bot.message_handler(func=lambda message: message.text in [
    '➕ Добавить админа', '➖ Удалить админа', '📋 Список админов',
    '🔙 В админ-панель'
])
def handle_admin_management_buttons(message):
    user_id = message.from_user.id

    if not db.is_admin(user_id):
        return

    # Очищаем состояние
    if user_id in user_states:
        del user_states[user_id]

    if message.text == '➕ Добавить админа':
        user_states[user_id] = 'waiting_for_admin_id'
        bot.send_message(message.chat.id,
                         "👤 Добавление администратора\n\n"
                         "Отправьте user_id пользователя:\n\n"
                         "💡 Как найти user_id?\n"
                         "1. Попросите пользователя отправить /myid\n"
                         "2. Или используйте @userinfobot\n\n"
                         "📝 Отправьте user_id:",
                         reply_markup=create_back_keyboard())

    elif message.text == '➖ Удалить админа':
        admins = db.get_admins()

        if len(admins) <= 1:
            bot.send_message(message.chat.id,
                             "❌ Нельзя удалить последнего администратора!\n\n"
                             "В системе должен остаться хотя бы один админ.")
            return

        admins_text = "👑 Текущие администраторы:\n\n"
        for admin in admins:
            admins_text += (
                f"• {admin.get('first_name', 'No name')} (@{admin.get('username', 'нет')})\n"
                f"  ID: {admin['user_id']}\n\n"
            )

        admins_text += "📝 Отправьте user_id для удаления:"

        user_states[user_id] = 'waiting_for_remove_admin_id'
        bot.send_message(message.chat.id, admins_text,
                         reply_markup=create_back_keyboard())

    elif message.text == '📋 Список админов':
        admins = db.get_admins()

        if not admins:
            bot.send_message(message.chat.id, "❌ Нет администраторов.")
            return

        admins_text = "👑 Список администраторов:\n\n"
        for i, admin in enumerate(admins, 1):
            created_at = admin.get('created_at', '')[:10] if admin.get('created_at') else 'Неизвестно'
            admins_text += (
                f"{i}. {admin.get('first_name', 'No name')} (@{admin.get('username', 'нет')})\n"
                f"   ID: {admin['user_id']}\n"
                f"   Дата: {created_at}\n\n"
            )

        bot.send_message(message.chat.id, admins_text)

    elif message.text == '🔙 В админ-панель':
        admin_command(message)


# Обработчики экспорта данных
@bot.message_handler(func=lambda message: message.text in [
    '📊 Экспорт в JSON', '📈 Экспорт в CSV', '🔙 В админ-панель'
])
def handle_admin_export_buttons(message):
    user_id = message.from_user.id

    if not db.is_admin(user_id):
        return

    # Очищаем состояние
    if user_id in user_states:
        del user_states[user_id]

    if message.text == '📊 Экспорт в JSON':
        try:
            bot.send_message(message.chat.id, "🔄 Подготавливаю JSON экспорт...")
            json_data = db.export_data_json()

            # Сохраняем во временный файл
            filename = f"temp/export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(json_data)

            # Отправляем файл
            with open(filename, 'rb') as f:
                bot.send_document(message.chat.id, f,
                                  caption="📊 Экспорт данных в JSON\n\n"
                                          f"📁 Файл: {os.path.basename(filename)}")

            # Удаляем временный файл
            os.remove(filename)

        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка при экспорте JSON: {str(e)}")

    elif message.text == '📈 Экспорт в CSV':
        try:
            bot.send_message(message.chat.id, "🔄 Подготавливаю CSV экспорт...")
            csv_data = db.export_data_csv()

            # Сохраняем во временный файл
            filename = f"temp/export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(csv_data)

            # Отправляем файл
            with open(filename, 'rb') as f:
                bot.send_document(message.chat.id, f,
                                  caption="📈 Экспорт данных в CSV\n\n"
                                          f"📁 Файл: {os.path.basename(filename)}")

            # Удаляем временный файл
            os.remove(filename)

        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка при экспорте CSV: {str(e)}")

    elif message.text == '🔙 В админ-панель':
        admin_command(message)


# ИСПРАВЛЕННЫЕ ОБРАБОТЧИКИ ОЧИСТКИ ДАННЫХ
@bot.message_handler(func=lambda message: message.text in [
    '🗑️ Очистить всю историю', '📅 Очистить старые данные', '🔙 В админ-панель'
])
def handle_admin_cleanup_buttons(message):
    user_id = message.from_user.id

    if not db.is_admin(user_id):
        return

    # Очищаем состояние
    if user_id in user_states:
        del user_states[user_id]

    if message.text == '🗑️ Очистить всю историю':
        try:
            deleted_count = db.clear_history()
            bot.send_message(message.chat.id,
                             f"✅ История очищена!\n\n"
                             f"🗑️ Удалено записей: {deleted_count}")
        except Exception as e:
            bot.send_message(message.chat.id,
                             f"❌ Ошибка при очистке истории: {str(e)}")

    elif message.text == '📅 Очистить старые данные':
        bot.send_message(message.chat.id,
                         "📅 Очистка старых данных\n\n"
                         "Выберите период для очистки:",
                         reply_markup=create_cleanup_options_keyboard())

    elif message.text == '🔙 В админ-панель':
        admin_command(message)


# Обработчики выбора периода очистки
@bot.message_handler(func=lambda message: message.text in [
    '1 день', '7 дней', '30 дней', '90 дней', '🔙 Назад'
])
def handle_cleanup_period_buttons(message):
    user_id = message.from_user.id

    if not db.is_admin(user_id):
        return

    if message.text == '🔙 Назад':
        admin_command(message)
        return

    period_map = {
        '1 день': 1,
        '7 дней': 7,
        '30 дней': 30,
        '90 дней': 90
    }

    if message.text in period_map:
        days = period_map[message.text]
        try:
            deleted_count = db.clear_history(days)
            bot.send_message(message.chat.id,
                             f"✅ Очистка завершена!\n\n"
                             f"📅 Удалены данные старше {days} дней\n"
                             f"🗑️ Удалено записей: {deleted_count}",
                             reply_markup=create_admin_cleanup_keyboard())
        except Exception as e:
            bot.send_message(message.chat.id,
                             f"❌ Ошибка при очистке: {str(e)}",
                             reply_markup=create_admin_cleanup_keyboard())


# УНИВЕРСАЛЬНЫЙ ОБРАБОТЧИК ВВОДА ДАННЫХ ДЛЯ АДМИНКИ
@bot.message_handler(func=lambda message: message.from_user.id in user_states)
def handle_admin_input(message):
    user_id = message.from_user.id
    state = user_states.get(user_id)
    text = message.text.strip()

    if not db.is_admin(user_id):
        if user_id in user_states:
            del user_states[user_id]
        return

    # Обработка кнопки "Назад"
    if message.text == '🔙 Назад':
        if user_id in user_states:
            del user_states[user_id]
        admin_command(message)
        return

    try:
        # Обработка user_id для различных функций
        if state in ['waiting_for_admin_id', 'waiting_for_remove_admin_id',
                     'waiting_user_info', 'waiting_user_translations', 'waiting_user_translations_search']:

            target_user_id = int(text)

            if state == 'waiting_for_admin_id':
                if not db.user_exists(target_user_id):
                    bot.send_message(message.chat.id,
                                     f"❌ Пользователь не найден!\n\n"
                                     f"User ID: {target_user_id}\n\n"
                                     f"💡 Решение:\n"
                                     f"Пользователь должен сначала запустить бота (/start)")
                elif db.is_admin(target_user_id):
                    bot.send_message(message.chat.id,
                                     f"❌ Уже администратор!\n\n"
                                     f"Пользователь с ID {target_user_id} уже является админом.")
                else:
                    success = db.make_admin(target_user_id)
                    if success:
                        user_info = db.get_user_info(target_user_id)
                        user_name = user_info.get('first_name', 'Пользователь') if user_info else 'Пользователь'
                        bot.send_message(message.chat.id,
                                         f"✅ Успех!\n\n"
                                         f"Пользователь {user_name} (ID: {target_user_id}) теперь администратор!")
                    else:
                        bot.send_message(message.chat.id,
                                         f"❌ Ошибка!\n\n"
                                         f"Не удалось назначить администратора.")

            elif state == 'waiting_for_remove_admin_id':
                if target_user_id == user_id:
                    bot.send_message(message.chat.id,
                                     "❌ Нельзя удалить себя!\n\n"
                                     "Используйте эту функцию для удаления других администраторов.")
                elif not db.is_admin(target_user_id):
                    bot.send_message(message.chat.id,
                                     f"❌ Не администратор!\n\n"
                                     f"Пользователь с ID {target_user_id} не является админом.")
                else:
                    success = db.remove_admin(target_user_id)
                    if success:
                        user_info = db.get_user_info(target_user_id)
                        user_name = user_info.get('first_name', 'Пользователь') if user_info else 'Пользователь'
                        bot.send_message(message.chat.id,
                                         f"✅ Успех!\n\n"
                                         f"Пользователь {user_name} (ID: {target_user_id}) больше не администратор!")
                    else:
                        bot.send_message(message.chat.id,
                                         f"❌ Ошибка!\n\n"
                                         f"Не удалось удалить администратора.")

            elif state == 'waiting_user_info':
                user_info = db.get_user_info(target_user_id)
                if not user_info:
                    bot.send_message(message.chat.id,
                                     f"❌ Пользователь не найден!\n\n"
                                     f"User ID: {target_user_id}")
                else:
                    user_stats = db.get_user_stats(target_user_id)
                    created_at = user_info.get('created_at', '')[:16] if user_info.get('created_at') else 'Неизвестно'
                    info_text = (
                        f"👤 Информация о пользователе\n\n"
                        f"🆔 User ID: {user_info['user_id']}\n"
                        f"📛 Имя: {user_info.get('first_name', 'Не указано')}\n"
                        f"🔗 Username: @{user_info.get('username', 'нет')}\n"
                        f"🌍 Язык: {user_info.get('language_code', 'en')}\n"
                        f"👑 Статус: {'Администратор 👑' if user_info.get('is_admin') else 'Пользователь'}\n"
                        f"📅 Регистрация: {created_at}\n\n"
                        f"📊 Статистика:\n"
                        f"• Переводов: {user_stats.get('translation_count', 0)}\n"
                        f"• Языков: {user_stats.get('languages_count', 0)}\n"
                        f"• Последний перевод: {user_stats.get('last_translation', 'Нет переводов')}"
                    )
                    bot.send_message(message.chat.id, info_text)

            elif state in ['waiting_user_translations', 'waiting_user_translations_search']:
                translations = db.get_translations_by_user(target_user_id, limit=10)
                user_info = db.get_user_info(target_user_id)

                if not translations:
                    user_name = user_info.get('first_name',
                                              f"ID: {target_user_id}") if user_info else f"ID: {target_user_id}"
                    bot.send_message(message.chat.id,
                                     f"📭 Нет переводов\n\n"
                                     f"Пользователь {user_name} еще не делал переводов.")
                else:
                    user_name = user_info.get('first_name',
                                              f"ID: {target_user_id}") if user_info else f"ID: {target_user_id}"
                    translations_text = f"📜 Последние 10 переводов пользователя {user_name}:\n\n"

                    for i, trans in enumerate(translations, 1):
                        lang_to = get_lang_name(trans.get('target_lang', 'en'))
                        time_str = trans.get('timestamp', '')[:16] if trans.get('timestamp') else 'Неизвестно'

                        translations_text += (
                            f"{i}. {time_str}\n"
                            f"   {trans.get('source_lang', 'auto')} → {lang_to}\n"
                            f"   📝 {trans.get('original_text', '')[:50]}...\n\n"
                        )

                    bot.send_message(message.chat.id, translations_text)

        # Удаляем состояние после обработки
        if user_id in user_states:
            del user_states[user_id]

        # Возвращаем к соответствующей клавиатуре
        time.sleep(1)
        if state in ['waiting_user_info', 'waiting_user_translations', 'waiting_user_translations_search']:
            handle_admin_users_buttons(message)
        elif state in ['waiting_for_admin_id', 'waiting_for_remove_admin_id']:
            handle_admin_management_buttons(message)

    except ValueError:
        bot.send_message(message.chat.id,
                         "❌ Неверный формат!\n\n"
                         "User ID должен быть числом.\n"
                         "Пример: 123456789")
    except Exception as e:
        bot.send_message(message.chat.id,
                         f"❌ Ошибка!\n\n{str(e)}")
        if user_id in user_states:
            del user_states[user_id]


# ==================== ОСНОВНЫЕ ОБРАБОТЧИКИ ====================

@bot.message_handler(func=lambda message: message.text in [
    '🇬🇧 Английский', '🇩🇪 Немецкий', '🇫🇷 Французский',
    '🇪🇸 Испанский', '🇮🇹 Итальянский', '🇷🇺 Русский',
    '🇺🇦 Украинский', '🇵🇱 Польский', '🔙 Назад'
])
def handle_language_button(message):
    lang_map = {
        '🇬🇧 Английский': 'en',
        '🇩🇪 Немецкий': 'de',
        '🇫🇷 Французский': 'fr',
        '🇪🇸 Испанский': 'es',
        '🇮🇹 Итальянский': 'it',
        '🇷🇺 Русский': 'ru',
        '🇺🇦 Украинский': 'uk',
        '🇵🇱 Польский': 'pl'
    }

    user_id = message.from_user.id
    selected_lang = message.text

    if selected_lang == '🔙 Назад':
        start_message(message)
        return

    if selected_lang in lang_map:
        lang_code = lang_map[selected_lang]
        db.set_user_language(user_id, lang_code)

        bot.send_message(
            message.chat.id,
            f'✅ Язык установлен!\n\n'
            f'🌍 {selected_lang}\n\n'
            f'Теперь отправьте текст для перевода:',
            reply_markup=create_main_keyboard()
        )


@bot.message_handler(func=lambda message: message.text in [
    '🌍 Выбрать язык', '📝 Переводчик', '📜 Моя история',
    '📊 Моя статистика', '🆘 Помощь'
])
def handle_main_buttons(message):
    if message.text == '🌍 Выбрать язык':
        language_command(message)
    elif message.text == '📝 Переводчик':
        user_id = message.from_user.id
        current_lang = db.get_user_language(user_id)

        if current_lang:
            lang_name = get_lang_name(current_lang)
            bot.send_message(
                message.chat.id,
                f'✅ Готов к переводу!\n\n'
                f'🌍 Текущий язык: {lang_name}\n\n'
                f'Отправьте текст для перевода:'
            )
        else:
            bot.send_message(
                message.chat.id,
                '❌ Сначала выберите язык!\n\n'
                'Используйте кнопку "🌍 Выбрать язык"'
            )
    elif message.text == '📜 Моя история':
        history_command(message)
    elif message.text == '📊 Моя статистика':
        stats_command(message)
    elif message.text == '🆘 Помощь':
        help_command(message)


@bot.message_handler(content_types=['text'])
def handler_translate(message):
    """Обработка текста для перевода"""
    user_id = message.from_user.id

    # Пропускаем команды и кнопки
    if (message.text.startswith('/') or
            message.text in [
                '🇬🇧 Английский', '🇩🇪 Немецкий', '🇫🇷 Французский',
                '🇪🇸 Испанский', '🇮🇹 Итальянский', '🇷🇺 Русский',
                '🇺🇦 Украинский', '🇵🇱 Польский', '🔙 Назад',
                '🌍 Выбрать язык', '📝 Переводчик', '📜 Моя история',
                '📊 Моя статистика', '🆘 Помощь',
                '📈 Общая статистика', '👥 Управление пользователями', '📜 Просмотр переводов',
                '🌍 Популярные языки', '👑 Управление админами', '📤 Экспорт данных',
                '🔄 Очистка данных', '🔙 В главное меню', '➕ Добавить админа', '➖ Удалить админа',
                '📋 Список админов', '🔙 В админ-панель', '📋 Список пользователей', '👤 Инфо о пользователе',
                '📊 Переводы пользователя', '📜 Последние переводы', '🔍 Поиск по пользователю',
                '📅 Переводы за сегодня', '📊 Экспорт в JSON', '📈 Экспорт в CSV', '🗑️ Очистить всю историю',
                '📅 Очистить старые данные', '1 день', '7 дней', '30 дней', '90 дней'
            ]):
        return

    # Проверяем, выбрал ли пользователь язык
    target_lang = db.get_user_language(user_id)
    if not target_lang:
        bot.send_message(
            message.chat.id,
            '❌ Сначала выберите язык!\n\n'
            'Используйте команду /language или кнопку "🌍 Выбрать язык"',
            reply_markup=create_main_keyboard()
        )
        return

    try:
        user_text = message.text

        # Переводим текст
        translation = simple_translate(user_text, target_lang)

        # Сохраняем в историю
        db.add_translation(user_id, user_text, translation, 'auto', target_lang)

        # Формируем ответ
        lang_name = get_lang_name(target_lang)
        response = (
            f"🌍 Перевод выполнен!\n\n"
            f"📝 Исходный текст:\n"
            f"{user_text}\n\n"
            f"✅ Перевод ({lang_name}):\n"
            f"{translation}\n\n"
            f"💫 Для нового перевода просто отправьте текст"
        )

        bot.send_message(
            message.chat.id,
            response
        )

    except Exception as e:
        bot.send_message(
            message.chat.id,
            f'❌ Ошибка перевода!\n\n{str(e)}'
        )


def main():
    """Основная функция запуска бота"""
    print("🚀 Запуск улучшенного бота-переводчика...")
    print("📊 База данных: ВКЛЮЧЕНА")
    print("👑 Админ-панель: УЛУЧШЕННАЯ")
    print("🌍 Переводчик: АКТИВЕН")
    print("=" * 50)

    try:
        bot_info = bot.get_me()
        print(f"✅ Бот: @{bot_info.username}")
        print(f"🆔 ID: {bot_info.id}")
        print("🤖 Ожидание сообщений...")
        print("=" * 50)

        bot.polling(none_stop=True, interval=1, timeout=30)

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("🔄 Перезапуск через 5 секунд...")
        time.sleep(5)
        main()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
        sys.exit(0)