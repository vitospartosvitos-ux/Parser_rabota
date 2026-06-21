import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Ссылка на твою базу данных в облаке Render
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Таблица для постов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            post_id TEXT UNIQUE,
            post_type TEXT,
            channel TEXT,
            text TEXT,
            url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица для каналов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()

def get_channels():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM channels")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row[0] for row in rows]

def add_channel(username):
    # Умная очистка: если ты случайно вставишь ссылку, бот сам вырежет только имя канала
    username = username.replace('https://t.me/', '').replace('t.me/', '').replace('@', '').strip()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO channels (username) VALUES (%s) ON CONFLICT (username) DO NOTHING", (username,))
        conn.commit()
    except Exception as e:
        print(f"[!] Ошибка добавления канала: {e}")
    finally:
        cursor.close()
        conn.close()

def delete_channel(username):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Железобетонное удаление канала по его имени
        cursor.execute("DELETE FROM channels WHERE username = %s", (username,))
        conn.commit()
    except Exception as e:
        print(f"[!] Ошибка удаления канала: {e}")
    finally:
        cursor.close()
        conn.close()

def post_exists(post_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM posts WHERE post_id = %s", (post_id,))
    exists = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return exists

def save_post(post_id, post_type, channel, text, url):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO posts (post_id, post_type, channel, text, url)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (post_id) DO NOTHING
        ''', (post_id, post_type, channel, text, url))
        conn.commit()
    except Exception as e:
        print(f"[!] Ошибка сохранения поста: {e}")
    finally:
        cursor.close()
        conn.close()

def get_posts(limit=50):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT post_type, channel, text, url FROM posts ORDER BY id DESC LIMIT %s", (limit,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def get_stats():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM posts")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM posts WHERE post_type = 'ORDER'")
    orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM posts WHERE post_type = 'VACANCY'")
    vacancies = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    return {"total": total, "orders": orders, "vacancies": vacancies}