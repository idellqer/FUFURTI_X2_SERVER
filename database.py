import sqlite3


DB = "database.db"


def connect():
    return sqlite3.connect(DB)



def init_db():
    db = connect()
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        username TEXT
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount TEXT,
        photo TEXT,
        status TEXT DEFAULT 'waiting'
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chats(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        user_id INTEGER,
        active INTEGER DEFAULT 1
    )
    """)


    db.commit()
    db.close()



def add_user(user_id, username):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO users(user_id, username)
        VALUES(?,?)
        """,
        (user_id, username)
    )

    db.commit()
    db.close()



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

    db.commit()

    request_id = cursor.lastrowid

    db.close()

    return request_id



def get_request(request_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT *
        FROM requests
        WHERE id=?
        """,
        (request_id,)
    )

    result = cursor.fetchone()

    db.close()

    return result



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



def start_chat(admin_id, user_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO chats(admin_id,user_id)
        VALUES(?,?)
        """,
        (
            admin_id,
            user_id
        )
    )

    db.commit()
    db.close()



def get_chat_user(admin_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT user_id
        FROM chats
        WHERE admin_id=? AND active=1
        ORDER BY id DESC
        LIMIT 1
        """,
        (admin_id,)
    )

    result = cursor.fetchone()

    db.close()

    if result:
        return result[0]

    return None



def end_chat(admin_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE chats
        SET active=0
        WHERE admin_id=?
        """,
        (admin_id,)
    )

    db.commit()
    db.close()
