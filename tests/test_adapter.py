from __future__ import annotations

import inspect

from gunray.adapter import GunrayEvaluator
from gunray.conformance_adapter import GunrayConformanceEvaluator


def test_suite_bridge_uses_public_constructor_injection() -> None:
    source = inspect.getsource(GunrayEvaluator._suite_bridge)

    assert "._core" not in source
    assert "core=self" in source


def test_conformance_bridge_accepts_core_constructor_argument() -> None:
    core = GunrayEvaluator()

    bridge = GunrayConformanceEvaluator(core=core)

    assert bridge is not None
