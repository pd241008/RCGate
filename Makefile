# RC-Gate — stage driver for the M0-M7 build order (agent.md section 8).
# Each stage target runs the real command used at that milestone; `make stages`
# executes the whole pipeline in sequence. Data tables, caches and results are
# gitignored — everything below regenerates them from committed code + configs.

CONFIG_SYNTH ?= synthetic
CONFIG_RAG   ?= ragtruth
SEEDS        ?= 5
BOOTSTRAP    ?= 1000

.PHONY: help stages m0 m1 m2 m3 m4 m5 m6 m7 test lint fmt smoke train evaluate clean

help:
	@echo "Stages (agent.md build order):"
	@echo "  m0     - scaffold check: pytest green, ruff clean, train CLI answers"
	@echo "  m1     - build the synthetic signal table with planted structure"
	@echo "  m2     - baselines A0-A4 on synthetic data"
	@echo "  m3     - RC-Gate A7 + ablations A3/A5/A6"
	@echo "  m4     - full evaluation harness on synthetic (CIs, LOGO, heatmap)"
	@echo "  m5     - build the real RAGTruth signal table (cached extractors)"
	@echo "  m6     - full evaluation on RAGTruth"
	@echo "  m7     - glass-box demo, headless verification"
	@echo "  stages - run m0 -> m7 in order"
	@echo "Dev targets:"
	@echo "  test lint fmt smoke train evaluate clean"

# --- stages ---------------------------------------------------------------

m0: test lint
	python -m rcgate.train --help > /dev/null
	@echo "M0 ok: tests green, lint clean, train CLI answers."

m1:
	python -m rcgate.data.build --config $(CONFIG_SYNTH)
	@echo "M1 ok: synthetic table(s) built."

m2:
	@for v in A0 A1 A2 A3 A4; do \
		echo "== M2 $$v =="; \
		python -m rcgate.train --config $(CONFIG_SYNTH) --variant $$v --seeds $(SEEDS); \
	done
	@echo "M2 ok: baselines trained; check results/summary/$(CONFIG_SYNTH).md after m4."

m3:
	@for v in A3 A5 A6 A7; do \
		echo "== M3 $$v =="; \
		python -m rcgate.train --config $(CONFIG_SYNTH) --variant $$v --seeds $(SEEDS); \
	done
	@echo "M3 ok: RC-Gate + ablations trained."

m4:
	python -m rcgate.evaluate --config $(CONFIG_SYNTH) --bootstrap $(BOOTSTRAP)
	@echo "M4 ok: results/summary/$(CONFIG_SYNTH).md + JSON twin + gate heatmap written."

m5:
	python -m rcgate.data.build --config $(CONFIG_RAG)
	@echo "M5 ok: RAGTruth table(s) built (second run is served from cache)."

m6:
	python -m rcgate.evaluate --config $(CONFIG_RAG) --bootstrap $(BOOTSTRAP)
	@echo "M6 ok: results/summary/$(CONFIG_RAG).md + run artefacts written."

m7: m6
	python -m rcgate.demo.app --config $(CONFIG_RAG) \
		--question "According to the context, when was the constitution signed?" \
		--answer "The constitution was signed on 17 September 1787."
	@echo "M7 ok: headless demo ran against the newest A7 checkpoint."
	@echo "       Interactive UI: streamlit run rcgate/demo/app.py"

stages: m0 m1 m2 m3 m4 m5 m6 m7
	@echo "All stages M0-M7 complete."

# --- dev targets ----------------------------------------------------------

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
	python -m rcgate.train --config configs/$(CONFIG_SYNTH).yaml --all-variants --seeds $(SEEDS)

evaluate:
	python -m rcgate.evaluate --config configs/$(CONFIG_SYNTH).yaml --bootstrap $(BOOTSTRAP) --out results/summary/$(CONFIG_SYNTH).md

clean:
	rm -rf .pytest_cache .ruff_cache
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
