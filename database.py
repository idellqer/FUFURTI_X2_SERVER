import sqlite3


DB_NAME = "database.db"


def connect():
    return sqlite3.connect(DB_NAME)


def create_tables():
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount TEXT,
        photo_id TEXT,
        status TEXT DEFAULT 'new'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        sender TEXT,
        text TEXT
    )
    """)

    db.commit()
    db.close()


def add_user(user_id, username):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO users(user_id, username)
    VALUES (?, ?)
    """, (user_id, username))

    db.commit()
    db.close()


def create_request(user_id, amount, photo_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
    INSERT INTO requests(user_id, amount, photo_id)
    VALUES (?, ?, ?)
    """, (user_id, amount, photo_id))

    db.commit()

    request_id = cursor.lastrowid

    db.close()

    return request_id


def get_request(request_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
    SELECT * FROM requests
    WHERE id=?
    """, (request_id,))

    result = cursor.fetchone()

    db.close()

    return result


def close_request(request_id):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
    UPDATE requests
    SET status='closed'
    WHERE id=?
    """, (request_id,))

    db.commit()
    db.close()


def save_message(user_id, sender, text):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
    INSERT INTO messages(user_id, sender, text)
    VALUES (?, ?, ?)
    """, (user_id, sender, text))

    db.commit()
    db.close()
