import sys
import time


def progress(count: int, text: str = "Evaluating"):
    """
    Utility generator for tracking and reporting loop progress to stderr.

    Usage:
        for i in progress(total_count, text="Running matches"):
            run_match()
    """
    current = 0
    last_percent = -1
    start_time = time.perf_counter()

    while True:
        percent = 100 * current // count if count > 0 else 100
        if percent != last_percent or current >= count:
            elapsed = time.perf_counter() - start_time
            eta_str = ""
            if current > 0 and count > current:
                rate = current / elapsed
                remaining = (count - current) / rate if rate > 0 else 0
                eta_str = f" | ETA: {remaining:.1f}s"

            msg = f"\r{text}: {percent}% ({current}/{count}){eta_str}"
            sys.stderr.write(msg.ljust(75))
            sys.stderr.flush()
            last_percent = percent

        if current >= count:
            sys.stderr.write("\r" + " " * 75 + "\r")
            sys.stderr.flush()
            break

        yield current
        current += 1
