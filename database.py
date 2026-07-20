import sqlite3

DB_NAME = "reputation_base.db"

def init_db():
    """Создает таблицы базы данных при старте приложения."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Таблица карточек списков
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reputation_cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_id INTEGER UNIQUE,
        username TEXT,
        status TEXT NOT NULL,
        description TEXT,
        added_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Таблица отзывов / комментариев
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_id INTEGER NOT NULL,
        author_id INTEGER NOT NULL,
        comment_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    conn.commit()
    conn.close()

def get_card(target_id: int):
    """Ищет запись в базе по Telegram ID."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT status, description, username FROM reputation_cards WHERE target_id = ?", 
        (target_id,)
    )
    card = cursor.fetchone()
    conn.close()
    return card

def get_comments(target_id: int, limit: int = 5):
    """Получает список последних отзывов."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT author_id, comment_text, created_at FROM comments WHERE target_id = ? ORDER BY id DESC LIMIT ?", 
        (target_id, limit)
    )
    comments = cursor.fetchall()
    conn.close()
    return comments

def add_comment(target_id: int, author_id: int, text: str):
    """Сохраняет комментарий."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO comments (target_id, author_id, comment_text) VALUES (?, ?, ?)",
        (target_id, author_id, text)
    )
    conn.commit()
    conn.close()

def add_or_update_card(target_id: int, username: str, status: str, description: str, admin_id: int):
    """Добавляет пользователя в базы списков репутации."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO reputation_cards (target_id, username, status, description, added_by) 
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(target_id) DO UPDATE SET 
               username=excluded.username,
               status=excluded.status,
               description=excluded.description,
               added_by=excluded.added_by""",
        (target_id, username, status, description, admin_id)
    )
    conn.commit()
    conn.close()