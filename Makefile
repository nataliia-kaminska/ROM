.PHONY: help setup venv backend frontend worker scheduler test test-backend test-frontend build migrate docker-up docker-down clean

PYTHON := ./.venv/Scripts/python.exe
PIP := ./.venv/Scripts/pip.exe
FRONTEND_DIR := frontend

help:
	@echo "Research Opportunity Matcher commands"
	@echo "  make setup          Install backend and frontend dependencies"
	@echo "  make backend        Run FastAPI on 127.0.0.1:8000"
	@echo "  make frontend       Run Vite frontend on 127.0.0.1:3000"
	@echo "  make worker         Run RQ worker"
	@echo "  make scheduler      Run background scheduler"
	@echo "  make test           Run backend tests and frontend build"
	@echo "  make migrate        Apply Alembic migrations"
	@echo "  make docker-up      Start full Docker stack"
	@echo "  make docker-down    Stop Docker stack"

setup: venv
	$(PYTHON) -m pip install -e ".[dev]"
	cd $(FRONTEND_DIR) && npm install

venv:
	@if not exist .venv py -3.11 -m venv .venv

backend:
	$(PYTHON) -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

frontend:
	cd $(FRONTEND_DIR) && npm run dev

worker:
	$(PYTHON) -m app.workers.worker

scheduler:
	$(PYTHON) -m app.workers.scheduler

test: test-backend test-frontend

test-backend:
	$(PYTHON) -m pytest

test-frontend:
	cd $(FRONTEND_DIR) && npm run build

build: test-frontend

migrate:
	$(PYTHON) -m alembic upgrade head

docker-up:
	docker compose up --build

docker-down:
	docker compose down

clean:
	cd $(FRONTEND_DIR) && if exist dist rmdir /s /q dist
