from sqlite3 import DatabaseError
import psycopg2 as pg 
from os import getenv 

def _conn():
    try: 
        uri = getenv("DATABASE_RUI")
        return pg.connect(uri)
    except DatabaseError:
        raise DatabaseError("Failed to connect to database")
    

def get_user_data(email:str):
    try:
        query = f"SELECT * FROM users WHERE email = '{email}'"
        conn = _conn()
        curr = conn.cursor()
        curr.execute(query)
        data = curr.fetchone()
        curr.close()
        conn.close()
        return data 
    except:
        pass

def get_user_access(email):
    try:
        query = f"SELECT * FROM access WHERE email = '{email}'"
        conn = _conn()
        curr = conn.cursor()
        curr.execute(query)
        data = curr.fetchone()
        curr.close()
        conn.close()
        return data 
    except:
        pass 

def insert_into_access(locker_nr, email):
    try:
        query = f"INSERT INTO access ('locker_nr', 'email') VALUES ('locker_nr', 'email')"
        conn = _conn()
        curr = conn.cursor()
        curr.execute(query)
        data = curr.fetchone()
        curr.close()
        conn.close()
        return data
    except:
        pass 
def create_user(email, password):
    try:        
        query = f"INSERT INTO users ('email', 'password') VALUES ('{email}', '{password}')'"
        conn = _conn()
        curr = conn.cursor()
        curr.execute(query)
        data = curr.fetchone()
        curr.close()
        conn.close()
        return data 
    except:
        pass 
