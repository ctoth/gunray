"""Data fusion: three sources disagree, explicit source reliability wins.

Shows: Garcia & Simari 2004 §4.1 ``superiority`` relation used as a
source-reliability ordering when every rule has the same (single-fact)
body and thus ``GeneralizedSpecificity`` cannot discriminate. Three
sources disagree on Einstein's birth year; peer-reviewed biography is
trusted over the official record, and both are trusted over Wikipedia.

Multi-valued disagreement (``birth_year/2`` with different year
arguments) is awkward for the strong-negation machinery — the
``conflicts`` slot can encode it, but for a small finite set of
candidates the cleaner modelling is one zero-arity-on-year predicate
per candidate, with each defeasible rule strong-negating its rivals.
That is what this example does.

Source: Garcia & Simari 2004 §4.1 p.17 (user ``superiority``); the
preference criterion follows ``src/gunray/defeasible.py:134`` —
``CompositePreference(SuperiorityPreference, GeneralizedSpecificity)``.
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
        strict_rules=[],
        defeasible_rules=[
            # Wikipedia asserts 1879.
            Rule(
                id="d_wiki_1879",
                head="born_1879(X)",
                body=["wikipedia_says_1879(X)"],
            ),
            # Official record asserts 1880. Whenever it fires it also
            # denies the other candidate explicitly — these are
            # mutually exclusive years.
            Rule(
                id="d_official_1880",
                head="born_1880(X)",
                body=["official_record_says_1880(X)"],
            ),
            Rule(
                id="d_official_not_1879",
                head="~born_1879(X)",
                body=["official_record_says_1880(X)"],
            ),
            # Peer-reviewed biography asserts 1879 and denies 1880.
            Rule(
                id="d_bio_1879",
                head="born_1879(X)",
                body=["peer_reviewed_biography_says_1879(X)"],
            ),
            Rule(
                id="d_bio_not_1880",
                head="~born_1880(X)",
                body=["peer_reviewed_biography_says_1879(X)"],
            ),
            # Wikipedia also denies the official date when it fires.
            Rule(
                id="d_wiki_not_1880",
                head="~born_1880(X)",
                body=["wikipedia_says_1879(X)"],
            ),
        ],
        defeaters=[],
        presumptions=[],
        # Source reliability, transitively: biography > official > wiki.
        # All three rule bodies are singletons from disjoint source
        # predicates, so ``GeneralizedSpecificity`` calls them equally
        # specific and ``SuperiorityPreference`` is what orders them.
        superiority=[
            ("d_bio_1879", "d_official_1880"),
            ("d_bio_not_1880", "d_official_1880"),
            ("d_bio_1879", "d_wiki_1879"),  # sanity — same direction
            ("d_official_1880", "d_wiki_1879"),
            ("d_official_not_1879", "d_wiki_1879"),
        ],
        conflicts=[],
    )


def _born_1879(name: str) -> GroundAtom:
    return GroundAtom(predicate="born_1879", arguments=(name,))


def _born_1880(name: str) -> GroundAtom:
    return GroundAtom(predicate="born_1880", arguments=(name,))


# All three sources speak.
facts: PredicateFacts = {
    "wikipedia_says_1879": {("einstein",)},
    "official_record_says_1880": {("einstein",)},
    "peer_reviewed_biography_says_1879": {("einstein",)},
}
theory = _build_theory(facts)
criterion = CompositePreference(
    SuperiorityPreference(theory),
    GeneralizedSpecificity(theory),
)

einstein_1879 = _born_1879("einstein")
einstein_1880 = _born_1880("einstein")

result_1879 = answer(theory, einstein_1879, criterion)
result_1880 = answer(theory, einstein_1880, criterion)

assert result_1879 is Answer.YES, f"expected YES for born_1879, got {result_1879!r}"
assert result_1880 is Answer.NO, f"expected NO for born_1880, got {result_1880!r}"


if __name__ == "__main__":
    print("Data fusion — reconciling disagreeing sources by reliability")
    print("  d_wiki_1879:        born_1879(X)   <= wikipedia_says_1879(X)")
    print("  d_official_1880:    born_1880(X)   <= official_record_says_1880(X)")
    print("  d_official_~1879:  ~born_1879(X)   <= official_record_says_1880(X)")
    print("  d_bio_1879:         born_1879(X)   <= peer_reviewed_biography_says_1879(X)")
    print("  d_bio_~1880:       ~born_1880(X)   <= peer_reviewed_biography_says_1879(X)")
    print("  d_wiki_~1880:      ~born_1880(X)   <= wikipedia_says_1879(X)")
    print("  superiority: biography > official > wikipedia")
    print()
    print("All three sources present. Biography and wikipedia both say")
    print("1879, but the official record says 1880. Biography dominates")
    print("both rivals; the official record loses to biography, and")
    print("wikipedia's agreement with biography reinforces 1879.")
    print(f"  answer(born_1879(einstein)) = {result_1879.name}")
    print(f"  answer(born_1880(einstein)) = {result_1880.name}")
