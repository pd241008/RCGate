.PHONY: help test lint fmt train smoke evaluate all clean

help:
	@echo "test      - run pytest"
	@echo "lint      - run ruff check"
	@echo "fmt       - run ruff format"
	@echo "smoke     - build synthetic table, train A7 for 2 epochs, evaluate"
	@echo "train     - train every variant on synthetic data (5 seeds)"
	@echo "evaluate  - full evaluation harness incl. LOGO + gate heatmap"
	@echo "all       - test + lint + smoke"

test:
	pytest

lint:
	ruff check rcgate tests

fmt:
	ruff format rcgate tests

smoke:
	python -m rcgate.train --config configs/smoke.yaml
	python -m rcgate.evaluate --config configs/smoke.yaml

train:
	python -m rcgate.train --config configs/synthetic.yaml --all-variants --seeds 5

evaluate:
	python -m rcgate.evaluate --config configs/synthetic.yaml --bootstrap 1000 --out results/summary/synthetic.md

clean:
	rm -rf .pytest_cache .ruff_cache
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
