PY ?= python
export PYTHONPATH := src

.PHONY: all ingest run test
all: ingest run
ingest:
	$(PY) -m hyx.ingest
run:
	$(PY) -m hyx.pipeline
test:
	$(PY) -m pytest -q tests
