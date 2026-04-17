"""Config precedence: four-layer override cascade by strict specificity.

Shows: Garcia & Simari 2004 §4.1 ``GeneralizedSpecificity`` ordering a
chain of four defaults on feature-flag state. Each successive condition
strictly entails the previous one via the ``strict_rules`` slot, so
specificity alone — without a single ``superiority`` pair — picks the
most specific applicable rule.

Strict entailment chain (each left-hand side is the stronger condition):

    safe_mode_disables_kill_switch(X)
        -> kill_switch_forced_on(X)
        -> env_override_off(X)
        -> default_on(X)

Four defaults, alternating polarity, conclude on ``enabled(X)``:

    d1 (weakest):   enabled(X)  <= default_on(X)
    d2:            ~enabled(X)  <= env_override_off(X)
    d3:             enabled(X)  <= kill_switch_forced_on(X)
    d4 (strongest):~enabled(X)  <= safe_mode_disables_kill_switch(X)

Because each stronger rule's body strictly entails the weaker rule's
body, ``GeneralizedSpecificity`` (Simari & Loui 1992 Lemma 2.4) ranks
d4 > d3 > d2 > d1. The cascade is observable by toggling facts one
layer at a time.

Source: Garcia & Simari 2004 §4.1 p.17 (``GeneralizedSpecificity`` as
preference criterion); Simari & Loui 1992 Lemma 2.4. Preference
composition follows ``src/gunray/defeasible.py:134``.
"""

from __future__ import annotations

from gunray import (
    Answer,
    CompositePreference,
    DefeasibleTheory,
    GeneralizedSpecificity,
    Rule,
    SuperiorityPreference,
    answer,
)
from gunray.schema import PredicateFacts
from gunray.types import GroundAtom


def _build_theory(facts: PredicateFacts) -> DefeasibleTheory:
    return DefeasibleTheory(
        facts=facts,
        strict_rules=[
            # Strict chain: each stronger switch necessarily implies the
            # next weaker one. Asserting the strongest fact gives us
            # everything below it via Π.
            Rule(
                id="s1",
                head="default_on(X)",
                body=["env_override_off(X)"],
            ),
            Rule(
                id="s2",
                head="env_override_off(X)",
                body=["kill_switch_forced_on(X)"],
            ),
            Rule(
                id="s3",
                head="kill_switch_forced_on(X)",
                body=["safe_mode_disables_kill_switch(X)"],
            ),
        ],
        defeasible_rules=[
            Rule(id="d1", head="enabled(X)", body=["default_on(X)"]),
            Rule(id="d2", head="~enabled(X)", body=["env_override_off(X)"]),
            Rule(id="d3", head="enabled(X)", body=["kill_switch_forced_on(X)"]),
            Rule(
                id="d4",
                head="~enabled(X)",
                body=["safe_mode_disables_kill_switch(X)"],
            ),
        ],
        defeaters=[],
        presumptions=[],
        superiority=[],
        conflicts=[],
    )


def _enabled(name: str) -> GroundAtom:
    return GroundAtom(predicate="enabled", arguments=(name,))


def _criterion(theory: DefeasibleTheory) -> CompositePreference:
    return CompositePreference(
        SuperiorityPreference(theory),
        GeneralizedSpecificity(theory),
    )


def _run(facts: PredicateFacts) -> Answer:
    theory = _build_theory(facts)
    return answer(theory, _enabled("feat_x"), _criterion(theory))


# Scenario 1: default_on alone. Only d1 has a firing body.
facts_1: PredicateFacts = {"default_on": {("feat_x",)}}
result_1 = _run(facts_1)

# Scenario 2: env_override_off. Via s1, default_on also holds. d2 more
# specific than d1: disabled.
facts_2: PredicateFacts = {"env_override_off": {("feat_x",)}}
result_2 = _run(facts_2)

# Scenario 3: kill_switch_forced_on. Via s2, s1 also the weaker layers
# fire. d3 more specific than d2 and d1: re-enabled.
facts_3: PredicateFacts = {"kill_switch_forced_on": {("feat_x",)}}
result_3 = _run(facts_3)

# Scenario 4: safe_mode_disables_kill_switch. All strict layers fire;
# d4 is most specific: disabled.
facts_4: PredicateFacts = {"safe_mode_disables_kill_switch": {("feat_x",)}}
result_4 = _run(facts_4)

assert result_1 is Answer.YES, f"scenario 1: expected YES, got {result_1!r}"
assert result_2 is Answer.NO, f"scenario 2: expected NO, got {result_2!r}"
assert result_3 is Answer.YES, f"scenario 3: expected YES, got {result_3!r}"
assert result_4 is Answer.NO, f"scenario 4: expected NO, got {result_4!r}"


if __name__ == "__main__":
    print("Config precedence — feature-flag override cascade")
    print("  s1:  default_on(X)       :- env_override_off(X)             (strict)")
    print("  s2:  env_override_off(X) :- kill_switch_forced_on(X)        (strict)")
    print("  s3:  kill_switch_forced_on(X) :- safe_mode_disables_kill_switch(X) (strict)")
    print("  d1:   enabled(X)  <= default_on(X)")
    print("  d2:  ~enabled(X)  <= env_override_off(X)")
    print("  d3:   enabled(X)  <= kill_switch_forced_on(X)")
    print("  d4:  ~enabled(X)  <= safe_mode_disables_kill_switch(X)")
    print("  superiority: (none) — specificity orders d4 > d3 > d2 > d1")
    print()
    print("Scenario 1 — default_on only.")
    print(f"  answer(enabled(feat_x)) = {result_1.name}")
    print("Scenario 2 — env_override_off (entails default_on strictly).")
    print(f"  answer(enabled(feat_x)) = {result_2.name}")
    print("Scenario 3 — kill_switch_forced_on (entails env_override_off).")
    print(f"  answer(enabled(feat_x)) = {result_3.name}")
    print("Scenario 4 — safe_mode_disables_kill_switch (most specific).")
    print(f"  answer(enabled(feat_x)) = {result_4.name}")
