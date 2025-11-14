import sqlite3
import datetime
import json
import csv
from typing import Optional, Dict, List
from io import StringIO


class Database:
    def __init__(self, db_name='translator_bot.db'):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        """Создать соединение с базой данных"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Инициализировать таблицы в базе данных"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT DEFAULT 'en',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_admin BOOLEAN DEFAULT FALSE
            )
        ''')

        # Таблица истории переводов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS translation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                original_text TEXT,
                translated_text TEXT,
                source_lang TEXT,
                target_lang TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        conn.commit()
        conn.close()

    def add_user(self, user_id: int, username: str, first_name: str, last_name: str = ''):
        """Добавить нового пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Проверяем, является ли пользователь администратором из config
            from config import ADMIN_IDS
            is_admin = user_id in ADMIN_IDS

            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, is_admin) 
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, is_admin))

            conn.commit()
        except Exception as e:
            print(f"Ошибка при добавлении пользователя: {e}")
        finally:
            conn.close()

    def set_user_language(self, user_id: int, language_code: str):
        """Установить язык пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                UPDATE users SET language_code = ? WHERE user_id = ?
            ''', (language_code, user_id))
            conn.commit()
        except Exception as e:
            print(f"Ошибка при установке языка: {e}")
        finally:
            conn.close()

    def get_user_language(self, user_id: int) -> Optional[str]:
        """Получить язык пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT language_code FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            return result['language_code'] if result else None
        except Exception as e:
            print(f"Ошибка при получении языка: {e}")
            return None
        finally:
            conn.close()

    def add_translation(self, user_id: int, original_text: str, translated_text: str,
                        source_lang: str, target_lang: str):
        """Добавить запись в историю переводов"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO translation_history 
                (user_id, original_text, translated_text, source_lang, target_lang)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, original_text, translated_text, source_lang, target_lang))
            conn.commit()
        except Exception as e:
            print(f"Ошибка при добавлении перевода: {e}")
        finally:
            conn.close()

    def get_user_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Получить историю переводов пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT * FROM translation_history 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (user_id, limit))

            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"Ошибка при получении истории: {e}")
            return []
        finally:
            conn.close()

    def get_all_users(self) -> List[Dict]:
        """Получить всех пользователей"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT user_id, username, first_name, last_name, language_code, created_at, is_admin
                FROM users 
                ORDER BY created_at DESC
            ''')

            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"Ошибка при получении пользователей: {e}")
            return []
        finally:
            conn.close()

    def get_admins(self) -> List[Dict]:
        """Получить всех администраторов"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT user_id, username, first_name, created_at, is_admin
                FROM users 
                WHERE is_admin = TRUE
                ORDER BY created_at DESC
            ''')

            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"Ошибка при получении админов: {e}")
            return []
        finally:
            conn.close()

    def make_admin(self, target_user_id: int) -> bool:
        """Сделать пользователя администратором"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                UPDATE users SET is_admin = TRUE WHERE user_id = ?
            ''', (target_user_id,))

            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error making admin: {e}")
            return False
        finally:
            conn.close()

    def remove_admin(self, target_user_id: int) -> bool:
        """Убрать права администратора"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                UPDATE users SET is_admin = FALSE WHERE user_id = ? AND user_id != ?
            ''', (target_user_id))  # Нельзя удалить главного админа

            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error removing admin: {e}")
            return False
        finally:
            conn.close()

    def get_recent_translations(self, limit: int = 50) -> List[Dict]:
        """Получить последние переводы"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT th.*, u.username, u.first_name, u.is_admin
                FROM translation_history th
                LEFT JOIN users u ON th.user_id = u.user_id
                ORDER BY th.timestamp DESC 
                LIMIT ?
            ''', (limit,))

            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"Ошибка при получении переводов: {e}")
            return []
        finally:
            conn.close()

    def get_translations_by_user(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Получить переводы конкретного пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT * FROM translation_history 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (user_id, limit))

            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"Ошибка при получении переводов пользователя: {e}")
            return []
        finally:
            conn.close()

    def get_translations_by_date(self, date: str) -> List[Dict]:
        """Получить переводы за конкретную дату"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT th.*, u.first_name 
                FROM translation_history th
                LEFT JOIN users u ON th.user_id = u.user_id
                WHERE date(th.timestamp) = ?
                ORDER BY th.timestamp DESC
            ''', (date,))

            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"Ошибка при получении переводов по дате: {e}")
            return []
        finally:
            conn.close()

    def get_user_stats(self, user_id: int) -> Dict:
        """Получить статистику пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT COUNT(*) as count FROM translation_history WHERE user_id = ?', (user_id,))
            translation_result = cursor.fetchone()
            translation_count = translation_result['count'] if translation_result else 0

            cursor.execute('SELECT timestamp FROM translation_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1',
                           (user_id,))
            last_translation_result = cursor.fetchone()
            last_translation = last_translation_result['timestamp'][:16] if last_translation_result else 'Нет переводов'

            cursor.execute('SELECT COUNT(DISTINCT target_lang) as langs FROM translation_history WHERE user_id = ?',
                           (user_id,))
            languages_result = cursor.fetchone()
            languages_count = languages_result['langs'] if languages_result else 0

            return {
                'translation_count': translation_count,
                'languages_count': languages_count,
                'last_translation': last_translation
            }
        except Exception as e:
            print(f"Ошибка при получении статистики: {e}")
            return {
                'translation_count': 0,
                'languages_count': 0,
                'last_translation': 'Нет переводов'
            }
        finally:
            conn.close()

    def get_global_stats(self) -> Dict:
        """Получить глобальную статистику"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT COUNT(*) as count FROM users')
            users_result = cursor.fetchone()
            users_count = users_result['count'] if users_result else 0

            cursor.execute('SELECT COUNT(*) as count FROM users WHERE is_admin = TRUE')
            admins_result = cursor.fetchone()
            admins_count = admins_result['count'] if admins_result else 0

            cursor.execute('SELECT COUNT(*) as count FROM translation_history')
            translations_result = cursor.fetchone()
            translations_count = translations_result['count'] if translations_result else 0

            cursor.execute(
                'SELECT COUNT(DISTINCT user_id) as active FROM translation_history WHERE date(timestamp) = date("now")')
            active_today_result = cursor.fetchone()
            active_today = active_today_result['active'] if active_today_result else 0

            cursor.execute(
                'SELECT COUNT(DISTINCT user_id) as active FROM translation_history WHERE date(timestamp) >= date("now", "-7 days")')
            active_week_result = cursor.fetchone()
            active_week = active_week_result['active'] if active_week_result else 0

            # Самый активный пользователь
            cursor.execute('''
                SELECT u.first_name, u.username, COUNT(*) as count 
                FROM translation_history th 
                JOIN users u ON th.user_id = u.user_id 
                GROUP BY th.user_id 
                ORDER BY count DESC 
                LIMIT 1
            ''')
            top_user_result = cursor.fetchone()

            top_user = "Нет данных"
            if top_user_result:
                top_user = f"{top_user_result['first_name'] or 'Пользователь'} (@{top_user_result['username'] or 'нет'}) - {top_user_result['count']} переводов"

            return {
                'users_count': users_count,
                'admins_count': admins_count,
                'translations_count': translations_count,
                'active_today': active_today,
                'active_week': active_week,
                'top_user': top_user
            }
        except Exception as e:
            print(f"Ошибка при получении глобальной статистики: {e}")
            return {
                'users_count': 0,
                'admins_count': 0,
                'translations_count': 0,
                'active_today': 0,
                'active_week': 0,
                'top_user': "Нет данных"
            }
        finally:
            conn.close()

    def is_admin(self, user_id: int) -> bool:
        """Проверить, является ли пользователь администратором"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT is_admin FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            return result['is_admin'] if result else False
        except Exception as e:
            print(f"Ошибка при проверке админа: {e}")
            return False
        finally:
            conn.close()

    def user_exists(self, user_id: int) -> bool:
        """Проверить, существует ли пользователь"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            return result is not None
        except Exception as e:
            print(f"Ошибка при проверке пользователя: {e}")
            return False
        finally:
            conn.close()

    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Получить информацию о пользователе"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
        except Exception as e:
            print(f"Ошибка при получении информации о пользователе: {e}")
            return None
        finally:
            conn.close()

    def get_top_languages(self) -> List[Dict]:
        """Получить самые популярные языки"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT target_lang, COUNT(*) as count 
                FROM translation_history 
                GROUP BY target_lang 
                ORDER BY count DESC 
                LIMIT 10
            ''')

            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"Ошибка при получении топ языков: {e}")
            return []
        finally:
            conn.close()

    def clear_history(self, days: int = None) -> int:
        """Очистить историю переводов - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if days:
                cursor.execute('DELETE FROM translation_history WHERE timestamp < datetime("now", ?)', (f"-{days} days",))
            else:
                cursor.execute('DELETE FROM translation_history')

            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
        except Exception as e:
            print(f"Ошибка при очистке истории: {e}")
            return 0
        finally:
            conn.close()

    def export_data_json(self) -> str:
        """Экспорт данных в JSON"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Пользователи
            cursor.execute('SELECT * FROM users')
            users = []
            for row in cursor.fetchall():
                user = dict(row)
                # Конвертируем datetime в строку
                if 'created_at' in user:
                    user['created_at'] = str(user['created_at'])
                users.append(user)

            # История переводов
            cursor.execute('SELECT * FROM translation_history ORDER BY timestamp DESC LIMIT 1000')
            translations = []
            for row in cursor.fetchall():
                trans = dict(row)
                # Конвертируем datetime в строку
                if 'timestamp' in trans:
                    trans['timestamp'] = str(trans['timestamp'])
                translations.append(trans)

            data = {
                'export_date': datetime.datetime.now().isoformat(),
                'users_count': len(users),
                'translations_count': len(translations),
                'users': users,
                'translations': translations
            }

            return json.dumps(data, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"Ошибка при экспорте JSON: {e}")
            return '{"error": "Ошибка экспорта"}'
        finally:
            conn.close()

    def export_data_csv(self) -> str:
        """Экспорт данных в CSV"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Пользователи
            cursor.execute('SELECT * FROM users')
            users = [dict(row) for row in cursor.fetchall()]

            # История переводов
            cursor.execute('SELECT * FROM translation_history ORDER BY timestamp DESC LIMIT 1000')
            translations = [dict(row) for row in cursor.fetchall()]

            output = StringIO()
            writer = csv.writer(output)

            # Заголовки для пользователей
            writer.writerow(['=== ПОЛЬЗОВАТЕЛИ ==='])
            writer.writerow(['User ID', 'Username', 'First Name', 'Last Name', 'Language', 'Created At', 'Is Admin'])
            for user in users:
                writer.writerow([
                    user['user_id'],
                    user['username'] or '',
                    user['first_name'] or '',
                    user['last_name'] or '',
                    user['language_code'] or 'en',
                    user['created_at'],
                    'Да' if user.get('is_admin') else 'Нет'
                ])

            writer.writerow([])
            writer.writerow(['=== ПЕРЕВОДЫ ==='])
            writer.writerow(
                ['ID', 'User ID', 'Original Text', 'Translated Text', 'Source Lang', 'Target Lang', 'Timestamp'])
            for trans in translations:
                writer.writerow([
                    trans['id'],
                    trans['user_id'],
                    (trans['original_text'] or '')[:100],  # Ограничиваем длину текста
                    (trans['translated_text'] or '')[:100],
                    trans['source_lang'] or 'auto',
                    trans['target_lang'] or 'en',
                    trans['timestamp']
                ])

            return output.getvalue()
        except Exception as e:
            print(f"Ошибка при экспорте CSV: {e}")
            return "Ошибка экспорта"
        finally:
            conn.close()


# Глобальный экземпляр базы данных
db = Database()