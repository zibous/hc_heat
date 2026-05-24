"""Zentrales Logging-Setup für die Heizungsanwendung."""

import logging
import sys
from logging.handlers import RotatingFileHandler

from config.app_config import LogSettings, BASE_DIR


def setup_logging(settings: LogSettings) -> logging.Logger:
    """Konfiguriert das Logging basierend auf den Einstellungen.

    Returns:
        Root-Logger der Anwendung.
    """
    root = logging.getLogger("hc_haco2")
    root.setLevel(getattr(logging, settings.level.upper(), logging.INFO))

    # Bestehende Handler entfernen
    root.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-5s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if not settings.enabled:
        root.addHandler(logging.NullHandler())
        return root

    # Console Handler
    if settings.mode in ("console", "both"):
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(formatter)
        root.addHandler(console)

    # File Handler
    if settings.mode in ("file", "both"):
        log_dir = BASE_DIR / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / settings.file
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=settings.max_bytes,
            backupCount=settings.backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    return root
