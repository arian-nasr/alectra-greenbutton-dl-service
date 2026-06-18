import logging
from schemas import AlectraCredentials, DatabaseConfig, DownloadParameters
from utils import get_dates_last_2_weeks
import scrape_xml
import xml_ops
import db_ops
from asyncio import run

logger = logging.getLogger(__name__)


def alectra_ingestor(alectra_creds: AlectraCredentials, db_conf: DatabaseConfig):
    """
    Ingest electricity usage data from Alectra portal into the database.

    Args:
        alectra_creds: Alectra account credentials
        db_conf: Database connection configuration

    Raises:
        TimeoutError: If the operation times out (handled by scheduler)
        Exception: For other failures during ingestion
    """
    fetch_start_date, fetch_end_date = get_dates_last_2_weeks()
    logger.info(
        f"Fetching data from {fetch_start_date.strftime('%Y-%m-%d')} "
        f"to {fetch_end_date.strftime('%Y-%m-%d')}"
    )

    download_params = DownloadParameters(
        start_date=fetch_start_date,
        end_date=fetch_end_date,
        account_name=alectra_creds.account_name,
        account_number=alectra_creds.account_number,
        account_phone=alectra_creds.account_phone
    )

    try:
        logger.info("Starting XML download from Alectra portal")
        xml_file = run(scrape_xml.download_xml_files(download_params))
        logger.info("XML download completed successfully")
    except Exception as e:
        logger.error(f"Failed to download XML: {type(e).__name__}: {e}")
        raise

    try:
        logger.info("Extracting interval readings from XML")
        interval_readings = xml_ops.extract_interval_readings(xml_file)
        records = xml_ops.convert_to_database_records(interval_readings)
        logger.info(f"Extracted {len(records)} records from XML")
    except Exception as e:
        logger.error(f"Failed to parse XML: {type(e).__name__}: {e}")
        raise

    try:
        logger.info("Writing records to database")
        with db_ops.connect_db(**db_conf.model_dump()) as conn:
            db_ops.write_records_to_db(conn, records)
            latest_record_date = db_ops.get_latest_record_date(conn)
        logger.info(
            f"Successfully processed {len(records)} records. "
            f"Date range: {fetch_start_date.strftime('%Y-%m-%d')} to "
            f"{fetch_end_date.strftime('%Y-%m-%d')}"
        )
        if latest_record_date:
            logger.info(f"Latest record in database: {latest_record_date}")
    except Exception as e:
        logger.error(f"Failed to write to database: {type(e).__name__}: {e}")
        raise
