#* Variables
SHELL := /usr/bin/env bash
PYTHON := python
PYTHONPATH := `pwd`

#* Installation
.PHONY: install
install:
	poetry lock -n && poetry export --without-hashes > requirements.txt
	poetry install -n

.PHONY: build-remove
build-remove:
	rm -rf build/

.PHONY: format
format:
	poetry run black benchmark_keeper