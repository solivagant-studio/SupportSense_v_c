# PLAN TASK: 1 | STUDENT TASK PACK: Day 1 | EVIDENCE: ONB-01
# WHERE: convenience commands for the SupportSense stack and test suites
# DO: use `make test` before each gate and record the result in your execution evidence.
PY ?= .venv/Scripts/python.exe
COMPOSE ?= docker compose -f docker/docker-compose.yml

.PHONY: up down seed reset test load dashboard

up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

seed:
	curl -s -X POST http://localhost:8000/v1/admin/reset

reset:
	curl -s -X POST http://localhost:8000/v1/admin/reset

test:
	$(PY) -m pytest -v --html=reports/report.html --self-contained-html

load:
	$(PY) -m locust -f tests/load/locustfile.py --headless -u 50 -r 5 -t 5m

dashboard:
	$(PY) -m streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port 8501
