.PHONY: help venv activate install core-install fmt lint clean-lint test clean-test clean-pyc clean ui
.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

COLOUR_GREEN=\033[0;32m
COLOUR_RED=\033[0;31m
COLOUR_BLUE=\033[0;34m
END_COLOUR=\033[0m

help: ## Show the help
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

venv: ## Create venv
	@if [ -d ".venv" ]; then\
		echo "${COLOUR_RED}The venv already exists, please delete it manually first${END_COLOUR}";\
		false;\
	else\
		python3 -m venv .venv;\
	fi;

install: ## Install the dependencies and the core package
	python3 -m pip install -r requirements.txt
	python3 -m pip install -r requirements_test.txt
	python3 -m pip install ../dbdie_classes

core-install: ## Install the core package from a specific path
	pip install $(core-path)

fmt: ## [ruff] Format the code
	ruff format

lint: ## [ruff] Run lint checks
	ruff check --output-format=concise

clean-lint: ## [ruff] Remove cache
	rm -rf .ruff_cache

test: ## [pytest] Test the code and coverage
	python3 -m pytest --cov=app

clean-test: ## [pytest] Remove test and coverage artifacts
	rm -rf .pytest_cache
	rm -rf .coverage

clean-pyc: ## Remove Python compiled bytecode files
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name 'pycache' -exec rm -fr {} +

clean: ## Remove all lint, test, coverage and compiled Python artifacts
	make clean-lint
	make clean-test
	make clean-pyc

ui: ## [gradio] Run the UI on localhost
	python3 app/main.py
