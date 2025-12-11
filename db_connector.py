import sqlite3
from schemas import DatabaseRecord


def connect_db(db_name):
    return sqlite3.connect(db_name)

def initialize_database(conn):
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS usage_data (timestamp TEXT PRIMARY KEY, value_kwh REAL, cost REAL, tou INTEGER)")
    conn.commit()

def insert_usage_data(conn, record: DatabaseRecord):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO usage_data (timestamp, value_kwh, cost, tou) VALUES (?, ?, ?, ?)",
        (record.timestamp.isoformat(), record.value_kwh, record.cost, record.tou)
    )
    conn.commit()

