from datetime import datetime
import psycopg2
from schemas import DatabaseRecord

def connect_db(host, database, user, password):
    return psycopg2.connect(
        host=host,
        database=database,
        user=user,
        password=password
    )

def write_records_to_db(conn, records: list[DatabaseRecord]):
    with conn.cursor() as cursor:
        data = [
            (record.interval_start, record.usage, record.cost, record.tou)
            for record in records
        ]
        query = """
            INSERT INTO electricity_usage (interval_start, usage, cost, tou)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (interval_start) DO UPDATE
            SET usage = EXCLUDED.usage,
                cost = EXCLUDED.cost,
                tou = EXCLUDED.tou
        """
        cursor.executemany(query, data)
        conn.commit()

def get_latest_record_date(conn) -> datetime:
    with conn.cursor() as cursor:
        cursor.execute("SELECT MAX(interval_start) FROM electricity_usage")
        result = cursor.fetchone()
        return result[0] if result[0] is not None else None
