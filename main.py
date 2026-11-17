"""Scheduled GreenButton usage downloader."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from io import BytesIO
from sqlite3 import Connection
from time import sleep
from zoneinfo import ZoneInfo

from agent_flow import HumanInterventionRequired
from config import load_settings
from db_connector import connect_db, initialize_database, insert_usage_data
from download_xml import download_xml_files
from greenbutton import parse
from schemas import DatabaseRecord, DownloadParameters

log = logging.getLogger(__name__)


def calculate_dates_for_retrieval(
    bill_start_date: str, bill_end_date: str
) -> tuple[datetime, datetime, datetime, datetime]:
    def round_date_up(dt):
        if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
            return dt
        return (dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    def round_date_down(dt):
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    utc_bill_start_date = (
        datetime.strptime(bill_start_date, "%m-%d-%Y")
        .replace(tzinfo=ZoneInfo("America/Toronto"))
        .astimezone(ZoneInfo("UTC"))
    )
    utc_bill_end_date = (
        datetime.strptime(bill_end_date, "%m-%d-%Y")
        .replace(tzinfo=ZoneInfo("America/Toronto"))
        .astimezone(ZoneInfo("UTC"))
    )
    utc_retrieval_start_date = round_date_down(utc_bill_start_date)
    utc_retrieval_end_date = round_date_up(utc_bill_end_date)

    return utc_retrieval_start_date, utc_retrieval_end_date, utc_bill_start_date, utc_bill_end_date


def process_xml_file(conn: Connection, xml_file: BytesIO):
    def get_correct_meter_reading(meter_readings):
        for meterReading in meter_readings:
            if meterReading.readingType and meterReading.readingType.title == "KWH Interval Data":
                return meterReading
        raise Exception("KWH Interval Data meter reading not found")

    usagePoint = parse.parse_feed(xml_file)[0]
    meterReadings = usagePoint.meterReadings
    meterReading = get_correct_meter_reading(meterReadings)
    for intervalBlock in meterReading.intervalBlocks:
        for intervalReading in intervalBlock.intervalReadings:
            record = DatabaseRecord(
                timestamp=intervalReading.timePeriod.start,
                value_kwh=intervalReading.value,
                cost=intervalReading.cost,
                tou=intervalReading.tou,
            )
            insert_usage_data(conn, record)


def get_dates_last_2_weeks() -> tuple[datetime, datetime]:
    now = datetime.now(tz=ZoneInfo("America/Toronto"))
    return now - timedelta(weeks=2), now


def run_cycle(settings) -> None:
    start_date, end_date = get_dates_last_2_weeks()
    params = DownloadParameters(
        start_date=start_date,
        end_date=end_date,
        account_name=settings.account_name,
        account_number=settings.account_number,
        account_phone=settings.account_phone,
    )

    xml_file = asyncio.run(download_xml_files(params, settings))

    conn = connect_db(settings.db_path)
    try:
        initialize_database(conn)
        process_xml_file(conn, xml_file)
    finally:
        conn.close()

    log.info("Processed data from %s to %s", start_date, end_date)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = load_settings()
    settings.validate()

    failures = 0
    while True:
        try:
            run_cycle(settings)
            failures = 0
        except HumanInterventionRequired as exc:
            failures += 1
            log.error("Human intervention required: %s", exc)
        except Exception:
            failures += 1
            log.exception("Download cycle failed")

        backoff = min(settings.cycle_interval_s, 60 * (2 ** min(failures, 5)))
        delay = backoff if failures else settings.cycle_interval_s
        log.info("Next cycle in %s seconds", delay)
        sleep(delay)
