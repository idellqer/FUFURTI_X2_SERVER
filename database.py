import sqlite3
db=sqlite3.connect("requests.db")
cur=db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS requests(id INTEGER PRIMARY KEY,user_id INTEGER,amount TEXT,photo TEXT)")
db.commit()

def add_request(user_id, amount, photo):
    cur.execute("INSERT INTO requests(user_id,amount,photo) VALUES(?,?,?)",(user_id,amount,photo))
    db.commit()
