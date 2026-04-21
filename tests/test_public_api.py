"""Public API surface contract: pins what ``from gunray import ...`` exposes."""

from __future__ import annotations

import gunray


def test_preference_subclasses_exported() -> None:
    """README preference examples rely on these package-level exports."""

    from gunray import (  # noqa: F401
        CompositePreference,
        GeneralizedSpecificity,
        SuperiorityPreference,
    )

    assert "CompositePreference" in gunray.__all__
    assert "GeneralizedSpecificity" in gunray.__all__
    assert "SuperiorityPreference" in gunray.__all__


def test_ground_defeasible_rule_is_public() -> None:
    """Consumer integrations should not have to import from gunray.types."""

    from gunray import GroundDefeasibleRule  # noqa: F401

    assert "GroundDefeasibleRule" in gunray.__all__


def test_public_all_is_complete_and_sorted() -> None:
    """Every name in ``__all__`` exists, and the list stays sorted."""

    for name in gunray.__all__:
        assert hasattr(gunray, name), f"gunray.__all__ claims {name!r} but it is absent"
    assert gunray.__all__ == sorted(gunray.__all__)
