# database.py — kører ved opstart for at oprette tabeller og seed dummy-data
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///dummy.db")

engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)
db = Session()


class User(Base):
    __tablename__ = "users"
    id     = Column(Integer, primary_key=True)
    email  = Column(String(255), unique=True, nullable=False)
    passwd = Column(String(255), nullable=False)


class Locker(Base):
    __tablename__ = "lockers"
    id     = Column(Integer, primary_key=True)
    status = Column(String(50), default="available")


class Access(Base):
    __tablename__ = "access"
    id         = Column(Integer, primary_key=True)
    locker_nr  = Column(String(50), nullable=False)
    email      = Column(String(255), nullable=False)
    valid_until = Column(DateTime)


def seed_db():
    if db.query(Locker).first():
        print("Database allerede seeded")
        return

    print("Seeder database...")
    lockers = [Locker(status="available") for _ in range(5)]
    db.add_all(lockers)
    db.commit()
    print("Database seeded — 5 skabe oprettet")


def init_db():
    import time
    for attempt in range(10):
        try:
            Base.metadata.create_all(engine)
            seed_db()
            return
        except Exception as e:
            if attempt < 9:
                print(f"Database ikke klar, prøver igen om 2s... ({e})")
                time.sleep(2)
            else:
                raise
