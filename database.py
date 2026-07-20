import sqlite3

DB_NAME = "blacklists.db"

def init_db():
    """Создает таблицу для черного списка, если ее еще нет"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blacklist (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            reason TEXT,
            added_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_to_blacklist(user_id: int, username: str, reason: str, admin_id: int) -> bool:
    """Добавляет пользователя в черный список"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO blacklist (user_id, username, reason, added_by)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, reason, admin_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Ошибка БД: {e}")
        return False

def check_blacklist(user_id: int):
    """Проверяет, есть ли пользователь в черном списке"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT reason, created_at FROM blacklist WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result # Вернет (reason, created_at) или None