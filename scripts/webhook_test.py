#!/usr/bin/env python3
"""Einfacher Webhook-Testserver.

Empfängt POST-Requests und zeigt sie an.
Simuliert einen Home Assistant Webhook-Endpoint.

Ausführen auf einem beliebigen Server:
  python3 webhook_test.py [port]

Standard-Port: 8123
Endpoint: POST /api/webhook/<webhook_id>
"""

import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8123

GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length else ""

        ts = datetime.now().strftime("%H:%M:%S")
        print(f"\n{GREEN}[{ts}] POST {self.path}{RESET}")

        if body:
            try:
                data = json.loads(body)
                event = data.get("event", "?")
                print(f"  {YELLOW}Event: {event}{RESET}")
                for k, v in data.items():
                    if k != "event":
                        print(f"  {CYAN}{k}{RESET}: {v}")
            except json.JSONDecodeError:
                print(f"  Body: {body[:200]}")

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format: str, *args: object) -> None:
        pass  # Keine Standard-Logs


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), WebhookHandler)
    print(f"Webhook-Testserver gestartet auf Port {PORT}")
    print(f"Endpoint: POST http://0.0.0.0:{PORT}/api/webhook/<id>")
    print("Ctrl+C zum Beenden\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBeendet.")
