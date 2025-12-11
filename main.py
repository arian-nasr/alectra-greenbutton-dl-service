from dotenv import load_dotenv
import os
from time import sleep
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from greenbutton import parse
from db_connector import insert_usage_data
from sqlite3 import Connection
from schemas import DatabaseRecord, DownloadParameters
import asyncio
from io import BytesIO


load_dotenv()
account_name = os.getenv("ALECTRA_ACCOUNT_NAME")
account_number = os.getenv("ALECTRA_ACCOUNT_NUMBER")
account_phone = os.getenv("ALECTRA_ACCOUNT_PHONE")
db_path = os.getenv("USAGE_DB_PATH", "./usage_data.db")

def calculate_dates_for_retrieval(bill_start_date: str, bill_end_date: str) -> tuple[datetime, datetime, datetime, datetime]:

    def round_date_up(dt):
        if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
            return dt
        else:
            return (dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    def round_date_down(dt):
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    utc_bill_start_date = datetime.strptime(bill_start_date, '%m-%d-%Y').replace(tzinfo=ZoneInfo('America/Toronto')).astimezone(ZoneInfo('UTC'))
    utc_bill_end_date = datetime.strptime(bill_end_date, '%m-%d-%Y').replace(tzinfo=ZoneInfo('America/Toronto')).astimezone(ZoneInfo('UTC'))
    utc_retrieval_start_date = round_date_down(utc_bill_start_date)
    utc_retrieval_end_date = round_date_up(utc_bill_end_date)

    return utc_retrieval_start_date, utc_retrieval_end_date, utc_bill_start_date, utc_bill_end_date

def process_xml_file(conn: Connection, xml_file: BytesIO):

    def get_correct_meter_reading(meter_readings):
        for meterReading in meter_readings:
            if meterReading.readingType and meterReading.readingType.title == 'KWH Interval Data':
                return meterReading
        raise Exception("KWH Interval Data meter reading not found")

    usagePoint = parse.parse_feed(xml_file)[0]
    meterReadings = usagePoint.meterReadings
    meterReading = get_correct_meter_reading(meterReadings)
    intervalBlocks = meterReading.intervalBlocks
    for intervalBlock in intervalBlocks:
        for intervalReading in intervalBlock.intervalReadings:
            timestamp = intervalReading.timePeriod.start
            value_kwh = intervalReading.value
            cost = intervalReading.cost
            tou = intervalReading.tou

            record = DatabaseRecord(
                timestamp=timestamp,
                value_kwh=value_kwh,
                cost=cost,
                tou=tou
            )
            insert_usage_data(conn, record)

def get_dates_last_2_weeks() -> tuple[datetime, datetime]:
    now = datetime.now(tz=ZoneInfo('America/Toronto'))
    two_weeks_ago = now - timedelta(weeks=2)
    return two_weeks_ago, now


if __name__ == "__main__":
    while True:
        from download_xml import download_xml_files
        from db_connector import connect_db, initialize_database

        start_date, end_date = get_dates_last_2_weeks()

        download_params = DownloadParameters(
            start_date=start_date,
            end_date=end_date,
            account_name=account_name,
            account_number=account_number,
            account_phone=account_phone
        )

        xml_file = asyncio.run(download_xml_files(download_params))


        conn = connect_db(db_path)
        initialize_database(conn)

        process_xml_file(conn, xml_file)

        conn.close()

        print(f"Processed data from {start_date} to {end_date}. Waiting for next cycle...")
        sleep(4 * 60 * 60)