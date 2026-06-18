import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Callable, Any

logger = logging.getLogger(__name__)


class ScheduledIngestor:
    """
    A threaded scheduler that runs a callback function at regular intervals
    with timeout protection and graceful shutdown handling.
    """

    def __init__(
        self,
        callback: Callable[..., Any],
        interval_seconds: float,
        timeout_seconds: float,
        callback_args: tuple = (),
        callback_kwargs: dict = None,
        prevent_overlap: bool = True
    ):
        """
        Initialize the scheduled ingestor.

        Args:
            callback: The function to execute on schedule
            interval_seconds: Time between executions in seconds
            timeout_seconds: Maximum time allowed for each execution
            callback_args: Positional arguments to pass to callback
            callback_kwargs: Keyword arguments to pass to callback
            prevent_overlap: If True, skip execution if previous run is still active
        """
        self.callback = callback
        self.interval_seconds = interval_seconds
        self.timeout_seconds = timeout_seconds
        self.callback_args = callback_args
        self.callback_kwargs = callback_kwargs or {}
        self.prevent_overlap = prevent_overlap

        self._stop_event = threading.Event()
        self._running_lock = threading.Lock()
        self._is_task_running = False
        self._timer: threading.Timer | None = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._started = False

    def start(self) -> None:
        """Start the scheduler and run the first execution immediately."""
        if self._started:
            logger.warning("Scheduler already started")
            return

        self._started = True
        self._stop_event.clear()
        logger.info(
            f"Scheduler started. Interval: {self.interval_seconds}s, "
            f"Timeout: {self.timeout_seconds}s"
        )
        # Run immediately on start
        self._execute()

    def stop(self, wait: bool = True) -> None:
        """
        Stop the scheduler gracefully.

        Args:
            wait: If True, wait for current execution to complete
        """
        logger.info("Stopping scheduler...")
        self._stop_event.set()

        if self._timer:
            self._timer.cancel()
            self._timer = None

        self._executor.shutdown(wait=wait, cancel_futures=not wait)
        self._started = False
        logger.info("Scheduler stopped")

    def _schedule_next(self) -> None:
        """Schedule the next execution."""
        if self._stop_event.is_set():
            return

        self._timer = threading.Timer(self.interval_seconds, self._execute)
        self._timer.daemon = True
        self._timer.start()
        logger.debug(f"Next execution scheduled in {self.interval_seconds}s")

    def _execute(self) -> None:
        """Execute the callback with timeout protection."""
        if self._stop_event.is_set():
            return

        # Check for overlap
        if self.prevent_overlap:
            with self._running_lock:
                if self._is_task_running:
                    logger.warning(
                        "Previous execution still running, skipping this cycle"
                    )
                    self._schedule_next()
                    return
                self._is_task_running = True

        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"[{timestamp}] Starting scheduled execution")

        try:
            future = self._executor.submit(
                self.callback, *self.callback_args, **self.callback_kwargs
            )
            future.result(timeout=self.timeout_seconds)
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"[{timestamp}] Execution completed successfully")

        except FuturesTimeoutError:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            logger.error(
                f"[{timestamp}] Execution timed out after {self.timeout_seconds}s"
            )
        except Exception as e:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            logger.error(f"[{timestamp}] Execution failed with error: {type(e).__name__}: {e}")
        finally:
            if self.prevent_overlap:
                with self._running_lock:
                    self._is_task_running = False
            self._schedule_next()

    def is_running(self) -> bool:
        """Check if the scheduler is currently running."""
        return self._started and not self._stop_event.is_set()

