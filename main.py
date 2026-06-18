import signal
import logging

if __name__ == "__main__":
    from dotenv import load_dotenv
    from os import getenv
    from schemas import DatabaseConfig, AlectraCredentials
    from ingestor import alectra_ingestor
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.executors.pool import ThreadPoolExecutor
    from datetime import datetime

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(__name__)

    load_dotenv()

    db_config = DatabaseConfig(
        database=getenv("DB_NAME"),
        user=getenv("DB_USER"),
        password=getenv("DB_PASSWORD"),
        host=getenv("DB_HOST")
    )

    alectra_credentials = AlectraCredentials(
        account_name=getenv("ALECTRA_ACCOUNT_NAME"),
        account_number=getenv("ALECTRA_ACCOUNT_NUMBER"),
        account_phone=getenv("ALECTRA_ACCOUNT_PHONE")
    )

    # Configuration
    INTERVAL_SECONDS = 3 * 60 * 60  # 1 hour
    TIMEOUT_SECONDS = 1 * 60 # 1 minute

    # Configure APScheduler
    executors = {
        'default': ThreadPoolExecutor(max_workers=1)
    }
    job_defaults = {
        'coalesce': True,  # Combine multiple missed runs into one
        'max_instances': 1,  # Prevent overlapping executions
        'misfire_grace_time': TIMEOUT_SECONDS  # Allow job to run if it missed its scheduled time within this window
    }
    scheduler = BlockingScheduler(executors=executors, job_defaults=job_defaults)

    # Add the ingestor job to run at regular intervals
    scheduler.add_job(
        func=alectra_ingestor,
        trigger='interval',
        seconds=INTERVAL_SECONDS,
        kwargs={
            "alectra_creds": alectra_credentials,
            "db_conf": db_config
        },
        id='alectra_ingestor',
        name='Alectra Electricity Usage Ingestor',
        replace_existing=True,
        next_run_time=datetime.now()
    )

    # Signal handlers for graceful shutdown
    def shutdown_handler(signum, frame):
        sig_name = signal.Signals(signum).name
        logger.info(f"Received {sig_name}, shutting down gracefully...")
        scheduler.shutdown(wait=True)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # Start scheduler (this blocks until shutdown)
    logger.info("Starting Alectra ingestor scheduler")
    logger.info(f"Interval: {INTERVAL_SECONDS}s, Timeout window: {TIMEOUT_SECONDS}s")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        logger.info("Application terminated")
