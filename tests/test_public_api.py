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


def test_propstore_facing_symbols_are_public() -> None:
    """Propstore-facing backend terms and parsers must not require private imports."""

    propstore_boundary_symbols = {
        "Constant": "current transitional grounding surface",
        "DefeasibleSections": "WS6 projection-boundary candidate",
        "FactTuple": "WS7 grounding-completion candidate",
        "GroundAtom": "WS6 projection-boundary candidate",
        "Scalar": "WS7 grounding-completion candidate",
        "Variable": "current transitional grounding surface",
        "parse_atom_text": "current transitional grounding surface",
    }

    missing = {
        name: classification
        for name, classification in propstore_boundary_symbols.items()
        if name not in gunray.__all__
    }
    assert missing == {}


def test_public_all_is_complete_and_sorted() -> None:
    """Every name in ``__all__`` exists, and the list stays sorted."""

    for name in gunray.__all__:
        assert hasattr(gunray, name), f"gunray.__all__ claims {name!r} but it is absent"
    assert gunray.__all__ == sorted(gunray.__all__)
