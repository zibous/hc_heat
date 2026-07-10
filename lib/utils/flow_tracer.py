"""Flow-Tracer: Zeichnet den Programmablauf auf (optional, per .env steuerbar)."""

import logging
from datetime import datetime

from config.app_config import BASE_DIR

logger = logging.getLogger(" hc_heat.flow")


class FlowTracer:
    """Schreibt Flow-Events in eine Datei für Debugging."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self._file_path = BASE_DIR / "logs" / "flow_trace.log"
        if self.enabled:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)

    def trace(self, component: str, message: str) -> None:
        """Schreibt einen Trace-Eintrag."""
        if not self.enabled:
            return
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        line = f"{ts} [{component}] {message}\n"
        try:
            with open(self._file_path, "a", encoding="utf-8") as f:
                f.write(line)
        except OSError:
            logger.warning("Flow-Trace konnte nicht geschrieben werden")
