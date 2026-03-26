SHELL := /bin/bash
.PHONY: setup run ngrok clean

VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

setup: ## Create venv and install dependencies
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt

run: ## Start the Slack bot locally
	set -a && source .env && set +a && $(PYTHON) app.py

ngrok: ## Start ngrok tunnel on port 3000
	ngrok http 3000

clean: ## Remove virtual environment
	rm -rf $(VENV)

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  make %-10s %s\n", $$1, $$2}'
