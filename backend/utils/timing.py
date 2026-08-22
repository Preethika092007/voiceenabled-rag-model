import time
from typing import Dict, Any

class PerfTimer:
    """
    Context manager for high-resolution monotonic timing.
    Records the elapsed time in milliseconds into the provided dictionary.
    """
    def __init__(self, timings_dict: Dict[str, float], key: str):
        self.timings_dict = timings_dict
        self.key = key
        self.start_time = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_ms = (time.perf_counter() - self.start_time) * 1000
        self.timings_dict[self.key] = elapsed_ms
