"""Black-box signals. Every module here reads text and returns numbers in [0, 1]."""

from .cache import Budget, BudgetExceeded, CacheStats, DiskCache, DryRunMiss, make_key

__all__ = ["Budget", "BudgetExceeded", "CacheStats", "DiskCache", "DryRunMiss", "make_key"]
