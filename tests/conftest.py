"""Shared fixtures, plus a hard network block: no test may touch the network.

The guard lives in ``conftest`` so it applies to every test in the tree, including any
added later. Tests that need a model call inject a fake into :class:`DiskCache`.
"""

from __future__ import annotations

import socket

import pytest


class NetworkBlocked(RuntimeError):
    pass


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Make any socket connection attempt an immediate, loud failure."""

    def _blocked(*args, **kwargs):
        raise NetworkBlocked("tests must not touch the network; inject a fake callable")

    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    yield


@pytest.fixture
def tiny_cache(tmp_path):
    """A DiskCache on a tmp dir with no budget, for hit/miss tests."""
    from rcgate.signals.cache import Budget, DiskCache

    return DiskCache(root=tmp_path / "cache", budget=Budget(dry_run=False))
