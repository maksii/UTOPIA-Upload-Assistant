.PHONY: test coverage lint

test:
	python -m pytest tests/ -v

coverage:
	python -m pytest tests/ --cov=src --cov-report=term-missing

lint:
	ruff check .
	ruff format --check .
