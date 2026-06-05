"""Dashboard HTTP-Server – liefert API-Daten und statische Dateien.

Leichtgewichtiger Server basierend auf http.server.
Kein Framework nötig, keine zusätzlichen Abhängigkeiten.
"""

import json
import logging
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Optional, Callable
from urllib.parse import urlparse, parse_qs

from config.app_config import AppConfig, BASE_DIR

logger = logging.getLogger("hc_haco2.dashboard")


class DashboardHandler(SimpleHTTPRequestHandler):
    """HTTP Handler für Dashboard API und statische Dateien."""

    # Wird von DashboardServer gesetzt
    base_path: str = "/dashboardhaco"
    static_dir: Path = BASE_DIR / "dashboard" / "static"
    get_snapshot: Optional[Callable] = None
    get_config: Optional[Callable] = None
    get_history: Optional[Callable] = None
    get_daily: Optional[Callable] = None
    get_kpi: Optional[Callable] = None

    def log_message(self, format: str, *args: object) -> None:
        logger.debug("HTTP %s", format % args)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        # Exakt base_path ohne Slash → Redirect auf base_path/
        if path == self.base_path:
            self.send_response(301)
            self.send_header("Location", self.base_path + "/")
            self.end_headers()
            return

        # Base-Path entfernen falls vorhanden
        if path.startswith(self.base_path):
            path = path[len(self.base_path) :]
        if not path:
            path = "/"

        # API-Routen
        if path == "/api/live":
            self._send_json(self._get_live_data())
        elif path == "/api/config":
            self._send_json(self._get_config_data())
        elif path == "/api/history":
            self._send_json(self._get_history_data())
        elif path.startswith("/api/daily"):
            params = parse_qs(parsed.query)
            if "from" in params and "to" in params:
                from_date = params["from"][0]
                to_date = params["to"][0]
                data = self.get_daily(0, from_date, to_date) if self.get_daily else []
            else:
                days = int(params.get("days", ["14"])[0])
                data = self.get_daily(days) if self.get_daily else []
            self._send_json({"data": data})
        elif path.startswith("/api/export"):
            params = parse_qs(parsed.query)
            days = int(params.get("days", ["30"])[0])
            self._send_csv(days)
        elif path == "/api/history-files":
            self._send_json(self._get_history_files())
        elif path.startswith("/api/history-file"):
            params = parse_qs(parsed.query)
            name = params.get("name", [""])[0]
            self._send_history_csv(name)
        elif path == "/api/kpidata":
            self._send_json(self._get_kpi_data())
        elif path == "/":
            self._serve_file("index.html")
        else:
            # Statische Dateien
            clean = path.lstrip("/")
            self._serve_file(clean)

    def _send_json(self, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_csv(self, days: int) -> None:
        """CSV-Export: Tagesverbrauch mit deutschem Dezimaltrennzeichen."""
        data = self.get_daily(days) if self.get_daily else []
        lines = ["Datum;Energie kWh;Heizung kWh;Warmwasser kWh;Gas m³;Brenner min"]
        for row in data:
            lines.append(
                f"{row['day']};"
                f"{str(row['energy_kwh']).replace('.', ',')};"
                f"{str(row['heat_kwh']).replace('.', ',')};"
                f"{str(row['dhw_kwh']).replace('.', ',')};"
                f"{str(row['gas_m3']).replace('.', ',')};"
                f"{row['burner_min']}"
            )
        body = "\n".join(lines).encode("utf-8-sig")  # BOM für Excel
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header(
            "Content-Disposition", f"attachment; filename=heizung_{days}d.csv"
        )
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, filename: str) -> None:
        file_path = self.static_dir / filename
        if not file_path.exists() or not file_path.is_file():
            self.send_error(404)
            return
        content_types = {
            ".html": "text/html; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
            ".json": "application/json",
        }
        ext = file_path.suffix.lower()
        ct = content_types.get(ext, "application/octet-stream")
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(body)

    def _get_live_data(self) -> dict:
        if not self.get_snapshot:
            return {"error": "no data"}
        return self.get_snapshot()

    def _get_config_data(self) -> dict:
        if not self.get_config:
            return {}
        return self.get_config()

    def _get_history_data(self) -> dict:
        if not self.get_history:
            return {"data": []}
        return {"data": self.get_history()}

    def _get_kpi_data(self) -> dict:
        """KPI-Daten für das zentrale Übersichts-Dashboard."""
        if not self.get_kpi:
            return {"app_id": "hc_heat", "status": "error", "hero": {"value": "–", "label": "Nicht verfügbar"}}
        try:
            return self.get_kpi()
        except Exception as e:
            logger.warning("KPI-Fehler: %s", e)
            return {"app_id": "hc_heat", "status": "error", "hero": {"value": "–", "label": str(e)}}

    def _get_history_files(self) -> dict:
        """Listet verfügbare History-CSV-Dateien."""
        history_dir = BASE_DIR / "data" / "history"
        if not history_dir.exists():
            return {"files": []}
        files = sorted(
            [f.name for f in history_dir.glob("*.csv")],
            reverse=True,
        )
        return {"files": files}

    def _send_history_csv(self, name: str) -> None:
        """Sendet eine History-CSV-Datei."""
        if not name or ".." in name or "/" in name:
            self.send_error(400)
            return
        history_dir = BASE_DIR / "data" / "history"
        filepath = history_dir / name
        if not filepath.exists() or not filepath.is_file():
            self.send_error(404)
            return
        body = filepath.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)


class DashboardServer:
    """Startet den Dashboard-Server in einem eigenen Thread."""

    def __init__(
        self,
        config: AppConfig,
        get_snapshot: Callable,
        get_config: Callable,
        get_history: Optional[Callable] = None,
        get_daily: Optional[Callable] = None,
        get_kpi: Optional[Callable] = None,
    ):
        self.port = config.app.dashboard_port
        # Base-Path normalisieren: mit / am Anfang, ohne / am Ende
        bp = config.app.dashboard_base_path.strip()
        if not bp.startswith("/"):
            bp = "/" + bp
        self.base_path = bp.rstrip("/")

        DashboardHandler.base_path = self.base_path
        DashboardHandler.static_dir = BASE_DIR / "dashboard" / "static"
        DashboardHandler.get_snapshot = staticmethod(get_snapshot)
        DashboardHandler.get_config = staticmethod(get_config)
        DashboardHandler.get_history = (
            staticmethod(get_history) if get_history else None
        )
        DashboardHandler.get_daily = staticmethod(get_daily) if get_daily else None
        DashboardHandler.get_kpi = staticmethod(get_kpi) if get_kpi else None

        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        try:
            self._server = HTTPServer(("0.0.0.0", self.port), DashboardHandler)
            self._thread = threading.Thread(
                target=self._server.serve_forever, daemon=True
            )
            self._thread.start()
            logger.info(
                "Dashboard gestartet: http://0.0.0.0:%d%s",
                self.port,
                self.base_path,
            )
        except Exception as e:
            logger.error("Dashboard konnte nicht gestartet werden: %s", e)

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            logger.info("Dashboard gestoppt")
