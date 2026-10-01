#!/usr/bin/env python3
"""HTTP load against the public school API. Stdlib only — no pip, no k6, no kubectl.

  python load-remote.py --lab 3
  python load-remote.py --lab 4
  python load-remote.py --lab 4 --workers 120 --seconds 300
"""
from __future__ import annotations

import argparse
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

LABS = {
    "3": "http://89.169.152.212/api/events",
    "4": "http://84.252.131.166/api/events",
}


def worker(url: str, stop_at: float) -> tuple[int, int]:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    ok = fail = 0
    while time.monotonic() < stop_at:
        try:
            with opener.open(url, timeout=8) as resp:
                resp.read()
                if 200 <= resp.status < 300:
                    ok += 1
                else:
                    fail += 1
        except (urllib.error.URLError, TimeoutError, OSError):
            fail += 1
    return ok, fail


def main() -> int:
    parser = argparse.ArgumentParser(description="Load the school API so HPA can scale")
    parser.add_argument("--lab", choices=LABS, default="4")
    parser.add_argument("--url", help="Override target URL")
    parser.add_argument("--workers", type=int, default=80)
    parser.add_argument("--seconds", type=int, default=240)
    args = parser.parse_args()
    url = args.url or LABS[args.lab]
    stop_at = time.monotonic() + args.seconds
    print(f"Load {url}  workers={args.workers}  duration={args.seconds}s")
    print("Watch HPA: kubectl -n school get hpa,pods -w")
    print("Ctrl+C stops this laptop; cluster HPA will scale down after ~1 min.")

    ok = fail = 0
    done = threading.Event()

    def progress() -> None:
        started = time.monotonic()
        while not done.wait(5):
            elapsed = int(time.monotonic() - started)
            print(f"  running {elapsed}/{args.seconds}s ...")

    t = threading.Thread(target=progress, daemon=True)
    t.start()
    try:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futs = [pool.submit(worker, url, stop_at) for _ in range(args.workers)]
            for fut in as_completed(futs):
                w_ok, w_fail = fut.result()
                ok += w_ok
                fail += w_fail
    except KeyboardInterrupt:
        print("\nStopped.")
        return 130
    finally:
        done.set()

    print(f"Done. ok={ok} fail={fail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
