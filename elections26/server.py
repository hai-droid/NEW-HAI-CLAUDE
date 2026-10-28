#!/usr/bin/env python3
"""מריץ את לוח התוצאות במחשב שלכם: משיכה ברקע + שרת אינטרנט קטן.

    python3 server.py              # http://localhost:8026
    python3 server.py --port 9000 --interval 30
"""

import argparse
import functools
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import fetcher


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # הדפדפן תמיד יקבל את הנתונים העדכניים.
        if self.path.startswith("/data/"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass


def fetch_loop(args, config):
    while True:
        try:
            fetcher.run_once(args, config)
        except Exception as e:  # noqa: BLE001 - ממשיכים לנסות
            print(f"שגיאה במשיכה: {e}")
        time.sleep(args.interval)


def main():
    config = fetcher.load_config()
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8026)
    ap.add_argument("--interval", type=int, default=config.get("refresh_seconds", 60))
    ap.add_argument("--no-fetch", action="store_true", help="רק להגיש את הקבצים, בלי למשוך")
    args = ap.parse_args()
    args.file = None

    if not args.no_fetch:
        threading.Thread(target=fetch_loop, args=(args, config), daemon=True).start()
    handler = functools.partial(Handler, directory=str(fetcher.ROOT))
    print(f"לוח התוצאות זמין בכתובת http://localhost:{args.port}")
    ThreadingHTTPServer(("", args.port), handler).serve_forever()


if __name__ == "__main__":
    main()
