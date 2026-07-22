import sqlite3


def connect():
    return sqlite3.connect("database.db")


def add_user(user_id, username):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        user_id INTEGER UNIQUE,
        username TEXT
    )
    """)

    cursor.execute(
        """
        INSERT OR REPLACE INTO users(user_id, username)
        VALUES (?,?)
        """,
        (user_id, username)
    )

    db.commit()
    db.close()


def save_request(user_id, amount, photo):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount TEXT,
        photo TEXT,
        status TEXT
    )
    """)

    cursor.execute(
        """
        INSERT INTO requests(user_id, amount, photo, status)
        VALUES(?,?,?,?)
        """,
        (user_id, amount, photo, "new")
    )

    db.commit()
    db.close()
    def create_request(user_id, amount, photo):
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount TEXT,
        photo TEXT,
        status TEXT
    )
    """)

    cursor.execute(
        """
        INSERT INTO requests(
            user_id,
            amount,
            photo,
            status
        )
        VALUES(?,?,?,?)
        """,
        (
            user_id,
            amount,
            photo,
            "waiting"
        )
    )

    db.commit()

    request_id = cursor.lastrowid

    db.close()

    return request_id
