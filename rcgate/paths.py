"""Filesystem layout. Every path in the project resolves from here."""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent

CONFIGS_DIR = PROJECT_ROOT / "configs"
RESULTS_DIR = PROJECT_ROOT / "results"
SUMMARY_DIR = RESULTS_DIR / "summary"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
TABLES_DIR = DATA_DIR / "signal_tables"
CACHE_DIR = PROJECT_ROOT / ".cache" / "llm"
#: Local CPU scorers (NLI, embeddings) are content-cached here, apart from the API cache:
#: they cost nothing, so they must not be charged against or blocked by the API budget.
COMPUTE_CACHE_DIR = PROJECT_ROOT / ".cache" / "compute"
MODEL_DIR = PROJECT_ROOT / ".cache" / "models"
PROMPTS_DIR = PACKAGE_ROOT / "prompts"

for _d in (SUMMARY_DIR, RAW_DIR, TABLES_DIR, CACHE_DIR, COMPUTE_CACHE_DIR, MODEL_DIR, PROMPTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)
