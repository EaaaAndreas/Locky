from sqlite3 import DatabaseError
import psycopg2 as pg
from psycopg2.extras import RealDictCursor
from os import getenv


def _conn():
    try:
        uri = getenv("DATABASE_URL")
        return pg.connect(uri)
    except DatabaseError:
        raise DatabaseError("Failed to connect to database")


def check_email_list():
    try:
        conn = _conn()
        curr = conn.cursor()
        curr.execute("SELECT email FROM users")
        rows = curr.fetchall()
        curr.close()
        conn.close()
        return [row[0] for row in rows]
    except DatabaseError:
        return []


def get_user_data(email: str):
    try:
        conn = _conn()
        curr = conn.cursor(cursor_factory=RealDictCursor)
        curr.execute("SELECT * FROM users WHERE email = %s", (email,))
        data = curr.fetchone()
        curr.close()
        conn.close()
        return data
    except DatabaseError:
        return None


def get_user_access(email):
    try:
        conn = _conn()
        curr = conn.cursor(cursor_factory=RealDictCursor)
        curr.execute("SELECT * FROM access WHERE email = %s", (email,))
        data = curr.fetchone()
        curr.close()
        conn.close()
        return data
    except DatabaseError:
        return None


def get_locker_access(locker_nr):
    try:
        conn = _conn()
        curr = conn.cursor(cursor_factory=RealDictCursor)
        curr.execute("SELECT * FROM access WHERE locker_nr = %s", (locker_nr,))
        data = curr.fetchone()
        curr.close()
        conn.close()
        return data
    except DatabaseError:
        return None


def get_all_booked_lockers():
    try:
        conn = _conn()
        curr = conn.cursor()
        curr.execute("SELECT locker_nr FROM access")
        rows = curr.fetchall()
        curr.close()
        conn.close()
        return {row[0] for row in rows}
    except DatabaseError:
        return set()


def insert_into_access(locker_nr, email):
    try:
        conn = _conn()
        curr = conn.cursor()
        curr.execute(
            "INSERT INTO access (locker_nr, email) VALUES (%s, %s)",
            (locker_nr, email),
        )
        conn.commit()
        curr.close()
        conn.close()
    except DatabaseError:
        pass


def release_locker(locker_nr):
    try:
        conn = _conn()
        curr = conn.cursor()
        curr.execute("DELETE FROM access WHERE locker_nr = %s", (locker_nr,))
        conn.commit()
        curr.close()
        conn.close()
    except DatabaseError:
        pass


def create_user(email, passwd):
    try:
        conn = _conn()
        curr = conn.cursor()
        curr.execute(
            "INSERT INTO users (email, passwd) VALUES (%s, %s)",
            (email, passwd),
        )
        conn.commit()
        curr.close()
        conn.close()
    except DatabaseError:
        pass
