import threading
import time

class Heartbeat:
    def __init__(self, interval: float, name: str = "heartbeat"):
        self.interval = interval
        self.name = name
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        # Initial heartbeat message
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Heartbeat: {self.name} is alive.")
        while not self._stop_event.wait(self.interval):
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Heartbeat: {self.name} is alive.")

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def is_running(self) -> bool:
        return self._thread.is_alive()