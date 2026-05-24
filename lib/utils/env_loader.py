"""Einfacher .env Loader ohne externe Abhängigkeiten."""

import os
from pathlib import Path


def load_dotenv(env_path: Path) -> None:
    """Lädt Variablen aus einer .env Datei in os.environ.

    Überschreibt keine bereits gesetzten Umgebungsvariablen.
    Unterstützt: KEY=VALUE, KEY="VALUE", Kommentare (#), Leerzeilen.
    """
    if not env_path.exists():
        return

    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Leerzeilen und Kommentare überspringen
            if not line or line.startswith("#"):
                continue
            # KEY=VALUE parsen
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Anführungszeichen entfernen
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            # Inline-Kommentare entfernen (nur bei nicht-gequoteten Werten)
            if "#" in value and not (line.count('"') >= 2 or line.count("'") >= 2):
                value = value.split("#")[0].strip()
            # Nicht überschreiben
            if key not in os.environ:
                os.environ[key] = value
