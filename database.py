import sqlite3
import time


DB = "database.db"


def connect():
    return sqlite3.connect(DB)



# ======================
# СОЗДАНИЕ ТАБЛИЦ
# ======================

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
        status TEXT DEFAULT 'open',
        created INTEGER
    )
    """)


    db.commit()
    db.close()



# ======================
# ПОЛЬЗОВАТЕЛИ
# ======================

def add_user(user_id, username):

    db = connect()
    cursor = db.cursor()


    cursor.execute("""
    INSERT OR IGNORE INTO users(id, username)
    VALUES(?,?)
    """,
    (
        user_id,
        username
    ))


    db.commit()
    db.close()



# ======================
# ПРОВЕРКА 12 ЧАСОВ
# ======================

def check_limit(user_id):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        "SELECT last_request FROM users WHERE id=?",
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



# ======================
# СОЗДАТЬ ЗАЯВКУ
# ======================

def create_request(user_id, amount, photo):

    db = connect()
    cursor = db.cursor()


    cursor.execute("""
    INSERT INTO requests(
        user_id,
        amount,
        photo,
        created
    )
    VALUES(?,?,?,?)
    """,
    (
        user_id,
        amount,
        photo,
        int(time.time())
    ))


    request_id = cursor.lastrowid


    cursor.execute("""
    UPDATE users
    SET last_request=?
    WHERE id=?
    """,
    (
        int(time.time()),
        user_id
    ))


    db.commit()
    db.close()


    return request_id



# ======================
# СБРОС ЛИМИТОВ
# ======================

def reset_limits():

    db = connect()
    cursor = db.cursor()


    cursor.execute("""
    UPDATE users
    SET last_request=0
    """)


    db.commit()
    db.close()



# ======================
# ЗАКРЫТИЕ ЗАЯВКИ
# ======================

def close_request(request_id):

    db = connect()
    cursor = db.cursor()


    cursor.execute("""
    UPDATE requests
    SET status='closed'
    WHERE id=?
    """,
    (request_id,))


    db.commit()
    db.close()
