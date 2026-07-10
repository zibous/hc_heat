# Makefile for  hc_heat (Heizungscontroller)
# --- 1. DYNAMISCHE PARAMETER & VARIABLEN ---
PROJECT_NAME = $(notdir $(CURDIR))
FORGEJO_IP   = 10.1.1.19
FORGEJO_PORT = 3143
FORGEJO_USER = peter
FORGEJO_URL  = http://$(FORGEJO_IP):$(FORGEJO_PORT)/$(FORGEJO_USER)/$(PROJECT_NAME).git

.DEFAULT_GOAL := help
.PHONY: run once simulate test install check build up down restart rebuild logs logs-tail ps stop start shell health clean resetdb prune help
IMAGE := hc-heat2
VERSION := 2.0.0

PYTHON := $(shell if [ -f /dockerapps/apps_v2/.venv/bin/python ]; then echo /dockerapps/apps_v2/.venv/bin/python; else echo python3; fi)
PIP := $(shell if [ -f /dockerapps/apps_v2/.venv/bin/pip ]; then echo /dockerapps/apps_v2/.venv/bin/pip; else echo pip3; fi)

# ---------------------------------------------------------
# Lokales Ausführen
# ---------------------------------------------------------

run: ## Startet die Anwendung lokal
	@$(PYTHON) app.py

once: ## Einmaliger Datenabruf (kein Loop)
	@$(PYTHON) app.py --once

simulate: ## 14 Tage Testdaten generieren + Dashboard starten
	@rm -f data/heating_sim.db
	@rm -f data/processed/*.json
	@$(PYTHON) scripts/simulate.py && APP_MODE=simulate $(PYTHON) app.py

simulate-csv: ## CSV-Daten importieren + Dashboard starten (echte Modi, Standard-Port: 5029)
	@$(PYTHON) scripts/import_csv_to_simdb.py $(CSV)
	@APP_MODE=simulate DASHBOARD_PORT=$(or $(DASHBOARD_PORT),5029) $(PYTHON) app.py

test: ## Offline-Tests ausführen
	@$(PYTHON) test_offline.py

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
	docker inspect --format='{{.State.Health.Status}}' hc-heat2

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

git-status: ## Zeigt die aktuelle Forgejo Server-Verbindung (Remote URL) an
	@echo "🔍 Überprüfe Git-Remote-Konfiguration..."
	@if ! git remote get-url origin >/dev/null 2>&1; then \
		echo "❌ Fehler: 'origin' ist noch nicht eingerichtet!"; \
		echo "👉 Bitte führe aus: make git-setup"; \
		exit 1; \
	fi
	@URL=$$(git remote get-url origin); \
	echo "🍏 Forgejo-Server ist aktiv verbunden!" ; \
	echo "🔗 Aktuelle URL: $$URL"

git-setup: ## Git-Verbindung zum Forgejo-Server automatisch einrichten oder korrigieren
	@echo "🛠️ Initialisiere Forgejo Server-Verbindung für '$(PROJECT_NAME)'..."
	@if ! git remote get-url origin >/dev/null 2>&1; then \
		git remote add origin $(FORGEJO_URL); \
		echo "🎉 Server-URL erfolgreich neu angelegt!"; \
	else \
		git remote set-url origin $(FORGEJO_URL); \
		echo "🔄 Bestehende Server-URL erfolgreich korrigiert!"; \
	fi
	@echo "🔗 Ziel-Adresse: $(FORGEJO_URL)"

git-update: git-status ## Git Forgejo Update durchführen (Normaler Zwischenstand)
	git add -A
	git commit -m "Update am $$(date +'%Y-%m-%d %H:%M')" || true
	git push -u origin main

git-release: git-status ## Neues Versions-Tag automatisch berechnen, erstellen und zu Forgejo pushen
	git add -A
	git commit -m "Release-Vorbereitung am $$(date +'%Y-%m-%d %H:%M')" || true
	git push origin main
	@LAST_TAG=$$(git describe --tags --abbrev=0 2>/dev/null || echo "v2.1.0"); \
	NEXT_TAG=$$(echo $$LAST_TAG | awk -F. '{print $$1"."$$2"."$$3+1}'); \
	echo "🍏 Letzte Version war: $$LAST_TAG"; \
	echo "⚡ Berechnete neue Version: $$NEXT_TAG"; \
	echo "📦 Erstelle Git-Tag $$NEXT_TAG mit aktuellem Zeitstempel..."; \
	git tag -a $$NEXT_TAG -m "Automatisches Release $$NEXT_TAG am $$(date +'%Y-%m-%d %H:%M') via Makefile"; \
	git push origin $$NEXT_TAG; \
	echo "🎉 Version $$NEXT_TAG erfolgreich an Forgejo übermittelt!"



compare: ## Vergleicht lokale Dateien mit Container-Inhalt
	@mkdir -p /tmp/hc-heat2_files
	@docker cp hc-heat2:/app/. /tmp/hc-heat2_files/
	@echo "─── Geänderte Dateien ───"
	@diff -qr --exclude="__pycache__" --exclude="*.pyc" --exclude=".git" \
		--exclude="data" --exclude="logs" --exclude=".env" --exclude=".ruff_cache" \
		./ /tmp/hc-heat2_files/ 2>/dev/null | sort || true
	@echo ""
	@echo "─── Nur lokal (neu/nicht im Container) ───"
	@diff -qr --exclude="__pycache__" --exclude="*.pyc" --exclude=".git" \
		--exclude="data" --exclude="logs" --exclude=".env" --exclude=".ruff_cache" \
		./ /tmp/hc-heat2_files/ 2>/dev/null | grep "Nur in \./" | sort || true
	@echo ""
	@echo "─── Nur im Container (lokal gelöscht) ───"
	@diff -qr --exclude="__pycache__" --exclude="*.pyc" --exclude=".git" \
		--exclude="data" --exclude="logs" --exclude=".env" --exclude=".ruff_cache" \
		./ /tmp/hc-heat2_files/ 2>/dev/null | grep "Nur in /tmp/" | sort || true
	@rm -rf /tmp/hc-heat2_files

diff-detail: ## Zeigt inhaltliche Unterschiede zum Container
	@mkdir -p /tmp/hc-heat2_files
	@docker cp hc-heat2:/app/. /tmp/hc-heat2_files/
	@diff -ur --exclude="__pycache__" --exclude="*.pyc" --exclude=".git" \
		--exclude="data" --exclude="logs" --exclude=".env" --exclude=".ruff_cache" \
		/tmp/hc-heat2_files/ ./ 2>/dev/null || true
	@rm -rf /tmp/hc-heat2_files

# 🔧 JS + CSS bundlen via Docker & esbuild (v2 Module)
jsbuild:
	@echo "📦 JS & CSS Bundling via Docker & esbuild..."
	@cp ../shared/themes/theme.css dashboard/static/css/theme.css
	@docker run --rm -v "$$(pwd)":/app -w /app node:20-alpine sh -c "\
		npx esbuild dashboard/static/js/v2/main.js --bundle --minify --sourcemap --format=esm --outfile=dashboard/static/js/v2/main.bundle.js && \
		npx esbuild dashboard/static/css/style2.css --bundle --minify --sourcemap --outfile=dashboard/static/css/style.bundle.css"
	@echo "✅ Fertig!"

jsclean:
	@echo "🧼 Bereinige produktive Build-Dateien..."
	@rm -f dashboard/static/js/v2/main.bundle.js
	@rm -f dashboard/static/js/v2/main.bundle.js.map
	@rm -f dashboard/static/css/style.bundle.css
	@rm -f dashboard/static/css/style.bundle.css.map
	@echo "✨ Verzeichnis ist wieder sauber."



# ---------------------------------------------------------
# Hilfe
# ---------------------------------------------------------

help: ## Diese Hilfe anzeigen
	@echo ""
	@echo " hc_heat – Heizungscontroller"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?##' Makefile | awk 'BEGIN {FS = ":.*?##"}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
