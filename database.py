import sqlite3
import time


DB = "bot.db"


def connect():
    return sqlite3.connect(DB)


def create_tables():
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT,
        last_request INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount TEXT,
        photo TEXT,
        status TEXT DEFAULT 'open'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chats(
        user_id INTEGER PRIMARY KEY
    )
    """)

    db.commit()
    db.close()



# =====================
# Пользователи
# =====================

def add_user(user_id, username):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO users(id, username)
        VALUES (?,?)
        """,
        (
            user_id,
            username
        )
    )

    db.commit()
    db.close()



# =====================
# Лимит 12 часов
# =====================

def check_limit(user_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT last_request 
        FROM users
        WHERE id=?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    db.close()


    if not result:
        return True


    last = result[0]

    if time.time() - last >= 43200:
        return True

    return False



def set_limit(user_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE users
        SET last_request=?
        WHERE id=?
        """,
        (
            int(time.time()),
            user_id
        )
    )

    db.commit()
    db.close()



def reset_limits():

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE users
        SET last_request=0
        """
    )

    db.commit()
    db.close()



# =====================
# Заявки
# =====================

def create_request(user_id, amount, photo):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO requests(
        user_id,
        amount,
        photo
        )
        VALUES(?,?,?)
        """,
        (
            user_id,
            amount,
            photo
        )
    )


    request_id = cursor.lastrowid


    db.commit()
    db.close()


    return request_id



def close_request(request_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE requests
        SET status='closed'
        WHERE id=?
        """,
        (request_id,)
    )


    db.commit()
    db.close()



# =====================
# Переписка
# =====================

def set_chat(user_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO chats(user_id)
        VALUES(?)
        """,
        (user_id,)
    )

    db.commit()
    db.close()



def get_chat():

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT user_id
        FROM chats
        LIMIT 1
        """
    )

    result = cursor.fetchone()

    db.close()


    if result:
        return result[0]

    return None



def clear_chat():

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM chats"
    )

    db.commit()
    db.close()
