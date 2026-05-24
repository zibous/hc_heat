# Makefile for hc_haco2 (Heizungscontroller)

.DEFAULT_GOAL := help
.PHONY: run once simulate test install check build up down restart rebuild logs logs-tail ps stop start shell health clean resetdb prune help
IMAGE := hc-haco2
VERSION := 2.0.0

PYTHON := ../.venv/bin/python
PIP := ../.venv/bin/pip

# ---------------------------------------------------------
# Lokales Ausführen
# ---------------------------------------------------------

run: ## Startet die Anwendung lokal
	@if [ -f ../.venv/bin/python ]; then \
		../.venv/bin/python app.py; \
	else \
		python3 app.py; \
	fi

once: ## Einmaliger Datenabruf (kein Loop)
	@if [ -f ../.venv/bin/python ]; then \
		../.venv/bin/python app.py --once; \
	else \
		python3 app.py --once; \
	fi

simulate: ## 14 Tage Testdaten generieren + Dashboard starten
	@rm -f data/heating_sim.db
	@rm -f data/processed/*.json
	@if [ -f ../.venv/bin/python ]; then \
		../.venv/bin/python scripts/simulate.py && APP_MODE=simulate ../.venv/bin/python app.py; \
	else \
		python3 scripts/simulate.py && APP_MODE=simulate python3 app.py; \
	fi

test: ## Offline-Tests ausführen
	@if [ -f ../.venv/bin/python ]; then \
		../.venv/bin/python test_offline.py; \
	else \
		python3 test_offline.py; \
	fi

install: ## Installiert Python-Abhängigkeiten
	pip install -r requirements.txt

check: ## Führt Ruff + Pyright Check aus
	@bash check.sh

# ---------------------------------------------------------
# Docker Commands
# ---------------------------------------------------------

build: ## Docker Image bauen
	docker compose build

up: ## Container starten
	docker compose up -d

up-mqtt: ## Container mit MQTT Broker starten
	docker compose --profile mqtt up -d

down: ## Container stoppen und entfernen
	docker compose down

restart: ## Container neu starten
	docker compose restart

rebuild: ## Neu bauen und starten
	docker compose up -d --build

logs: ## Logs anzeigen (follow)
	docker compose logs -f

logs-tail: ## Letzte 100 Zeilen
	docker compose logs --tail=100

ps: ## Laufende Container anzeigen
	docker compose ps

stop: ## Container stoppen
	docker compose stop

start: ## Gestoppte Container starten
	docker compose start

shell: ## Shell im Container öffnen
	docker compose exec hc-haco2 /bin/bash

health: ## Container Health prüfen
	docker inspect --format='{{.State.Health.Status}}' hc-haco2

# ---------------------------------------------------------
# Wartung
# ---------------------------------------------------------

clean: ## Cache und Temp-Dateien löschen
	@echo "🧹 Cleaning..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@rm -rf .pytest_cache .ruff_cache build dist *.egg-info
	@echo "✅ Done"

resetdb: ## Produktiv-DB löschen (Neustart)
	@echo "⚠️  Lösche Produktiv-Datenbank..."
	@rm -f data/heating.db data/heating.db.bak
	@echo "✅ heating.db gelöscht"

prune: ## Ungenutzte Docker-Ressourcen entfernen
	docker system prune -f

# ---------------------------------------------------------
# Hilfe
# ---------------------------------------------------------

help: ## Diese Hilfe anzeigen
	@echo ""
	@echo "hc_haco2 – Heizungscontroller"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?##' Makefile | awk 'BEGIN {FS = ":.*?##"}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
