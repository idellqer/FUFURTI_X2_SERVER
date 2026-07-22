import sqlite3
import time


DB = "database.db"


# =========================
# ПОДКЛЮЧЕНИЕ
# =========================

def connect():
    return sqlite3.connect(DB)



# =========================
# СОЗДАНИЕ ТАБЛИЦ
# =========================

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
        status TEXT
    )
    """)


    db.commit()
    db.close()



# =========================
# ДОБАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯ
# =========================

def add_user(user_id, username):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        INSERT OR IGNORE INTO users
        (id, username)
        VALUES (?,?)
        """,
        (
            user_id,
            username
        )
    )


    db.commit()
    db.close()



# =========================
# ПРОВЕРКА ЛИМИТА 12 ЧАСОВ
# =========================

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


    if last == 0:
        return True


    now = int(time.time())


    if now - last >= 43200:
        return True


    return False



# =========================
# УСТАНОВИТЬ ЛИМИТ
# =========================

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



# =========================
# СОЗДАНИЕ ЗАЯВКИ
# =========================

def create_request(
        user_id,
        amount,
        photo
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        INSERT INTO requests
        (
        user_id,
        amount,
        photo,
        status
        )
        VALUES (?,?,?,?)
        """,
        (
            user_id,
            amount,
            photo,
            "open"
        )
    )


    request_id = cursor.lastrowid


    db.commit()
    db.close()


    return request_id



# =========================
# ЗАКРЫТЬ ЗАЯВКУ
# =========================

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



# =========================
# СБРОС ВСЕХ ЛИМИТОВ
# =========================

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
