"""HistoryManager: Speichert und lädt HeatingSnapshots als JSON."""

import json
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import is_dataclass, asdict

from ..models.heating_snapshot import HeatingSnapshot

logger = logging.getLogger(" hc_heat.history")


class HistoryManager:
    """Speichert HeatingSnapshot-Objekte als JSON-Dateien."""

    def __init__(self, folder: str = "data/processed"):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)

    def _serialize(self, obj: object) -> object:
        """Rekursiver Serializer für Dataclasses."""
        if is_dataclass(obj) and not isinstance(obj, type):
            return {k: self._serialize(v) for k, v in asdict(obj).items()}
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: self._serialize(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._serialize(v) for v in obj]
        return obj

    def save_snapshot(self, snapshot: HeatingSnapshot) -> Path:
        """Speichert einen Snapshot als JSON-Datei."""
        ts = snapshot.timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        file_path = self.folder / f"{ts}.json"
        data = self._serialize(snapshot)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info("Snapshot gespeichert: %s", file_path.name)
        return file_path

    def list_snapshots(self) -> list[Path]:
        """Listet alle gespeicherten Snapshots."""
        return sorted(self.folder.glob("*.json"))

    def load_snapshot(self, file_path: Path) -> dict | None:
        """Lädt einen Snapshot als dict."""
        if not file_path.exists():
            logger.warning("Snapshot nicht gefunden: %s", file_path)
            return None
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
