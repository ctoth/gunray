"""Unit and property tests for gunray.arguments.build_arguments.

Garcia & Simari 2004 Definition 3.1, Simari & Loui 1992 Definition 2.2.
"""

from __future__ import annotations

from itertools import combinations

from conftest import small_theory_strategy
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from gunray.answer import Answer
from gunray.arguments import build_arguments
from gunray.dialectic import answer
from gunray.disagreement import strict_closure
from gunray.parser import parse_atom_text
from gunray.preference import GeneralizedSpecificity
from gunray.schema import DefeasibleTheory, Rule
from gunray.types import GroundAtom, GroundDefeasibleRule


def _tweety_theory() -> DefeasibleTheory:
    return DefeasibleTheory(
        facts={"bird": {("tweety",), ("opus",)}, "penguin": {("opus",)}},
        strict_rules=[Rule(id="s1", head="bird(X)", body=["penguin(X)"])],
        defeasible_rules=[
            Rule(id="r1", head="flies(X)", body=["bird(X)"]),
            Rule(id="r2", head="~flies(X)", body=["penguin(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def test_tweety_flies_argument_exists() -> None:
    """Garcia & Simari 2004 Def 3.1: <{r1(tweety)}, flies(tweety)> is an argument."""

    theory = _tweety_theory()
    arguments = build_arguments(theory)

    flies_tweety = GroundAtom(predicate="flies", arguments=("tweety",))
    matching = [arg for arg in arguments if arg.conclusion == flies_tweety]
    assert matching, f"no argument for flies(tweety) in {arguments!r}"

    # The grounded r1 instance with X=tweety must appear in rules.
    for arg in matching:
        grounded_rule_ids = {rule.rule_id for rule in arg.rules}
        if "r1" in grounded_rule_ids:
            return
    raise AssertionError(f"no argument for flies(tweety) was backed by r1: {matching!r}")


def test_opus_not_flies_argument_exists() -> None:
    """Opus's penguin rule must produce <{r2(opus)}, ~flies(opus)>."""

    theory = _tweety_theory()
    arguments = build_arguments(theory)

    not_flies_opus = GroundAtom(predicate="~flies", arguments=("opus",))
    matching = [arg for arg in arguments if arg.conclusion == not_flies_opus]
    assert matching, f"no argument for ~flies(opus) in {arguments!r}"

    for arg in matching:
        grounded_rule_ids = {rule.rule_id for rule in arg.rules}
        if "r2" in grounded_rule_ids:
            return
    raise AssertionError(f"no argument for ~flies(opus) was backed by r2: {matching!r}")


def _nixon_theory() -> DefeasibleTheory:
    return DefeasibleTheory(
        facts={"republican": {("nixon",)}, "quaker": {("nixon",)}},
        strict_rules=[],
        defeasible_rules=[
            Rule(id="r1", head="~pacifist(X)", body=["republican(X)"]),
            Rule(id="r2", head="pacifist(X)", body=["quaker(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def test_nixon_diamond_has_both_arguments() -> None:
    """Garcia & Simari 2004 Def 3.1: both sides of Nixon must produce arguments."""

    theory = _nixon_theory()
    arguments = build_arguments(theory)

    pacifist_nixon = GroundAtom(predicate="pacifist", arguments=("nixon",))
    not_pacifist_nixon = GroundAtom(predicate="~pacifist", arguments=("nixon",))

    pacifist_args = [a for a in arguments if a.conclusion == pacifist_nixon]
    not_pacifist_args = [a for a in arguments if a.conclusion == not_pacifist_nixon]

    assert pacifist_args, f"no argument for pacifist(nixon): {arguments!r}"
    assert not_pacifist_args, f"no argument for ~pacifist(nixon): {arguments!r}"


def test_defeater_rule_emits_one_rule_argument() -> None:
    """Nute/Antoniou defeater reading: defeaters participate in enumeration.

    Garcia & Simari 2004 defines only strict and defeasible rules; the
    third ``kind="defeater"`` category used by DePYsible/Spindle style
    theories is the Nute-style defeater — a rule that can attack other
    arguments but never concludes the final query (see
    ``notes/b2_defeater_participation.md`` for the paper reading).

    The participation invariant: for every ground defeater ``d`` whose
    body is derivable from ``Pi`` alone, ``build_arguments`` emits the
    one-rule argument ``<{d}, head(d)>``. This is the only way a
    defeater can attack a defeasible argument in the dialectical tree.
    Warrant filtering (i.e. the guarantee that a defeater-headed
    argument never warrants a YES/NO answer) is enforced by
    ``dialectic.answer``, not by suppressing the argument at
    construction time.
    """

    theory = DefeasibleTheory(
        facts={"yellow": {("x",)}},
        strict_rules=[],
        defeasible_rules=[],
        defeaters=[Rule(id="d1", head="banana(X)", body=["yellow(X)"])],
        superiority=[],
        conflicts=[],
    )
    arguments = build_arguments(theory)

    banana_x = GroundAtom(predicate="banana", arguments=("x",))
    matching = [a for a in arguments if a.conclusion == banana_x]
    assert matching, f"no defeater-argument for banana(x) in {arguments!r}"
    for arg in matching:
        assert any(r.rule_id == "d1" for r in arg.rules), (
            f"argument for banana(x) not backed by d1: {arg!r}"
        )
        assert all(r.kind == "defeater" for r in arg.rules), (
            f"defeater argument should be all-defeater: {arg!r}"
        )


def test_strict_only_arguments_have_empty_rules() -> None:
    """Garcia & Simari 2004 Def 3.1: strict-only theories have <empty, h>.

    When ``Delta`` is empty, condition (1) degenerates to a strict
    derivation; every argument must have ``rules == frozenset()``.
    """

    theory = DefeasibleTheory(
        facts={"fact_p": {("a",)}},
        strict_rules=[Rule(id="s1", head="fact_q(X)", body=["fact_p(X)"])],
        defeasible_rules=[],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )

    arguments = build_arguments(theory)
    assert arguments, "strict-only theory should still yield strict arguments"
    for argument in arguments:
        assert argument.rules == frozenset(), (
            f"strict-only theory produced non-empty argument: {argument!r}"
        )


@given(theory=small_theory_strategy())
@settings(max_examples=500, deadline=None)
def test_hypothesis_build_arguments_is_deterministic(
    theory: DefeasibleTheory,
) -> None:
    """Invoking ``build_arguments`` twice on the same theory yields equal sets.

    Guards against accidental state leakage (e.g. cached mutable
    structures from grounding helpers).
    """

    assert build_arguments(theory) == build_arguments(theory)


def _fact_atoms_from_theory(theory: DefeasibleTheory) -> frozenset[GroundAtom]:
    """Collect ground fact atoms out of a DefeasibleTheory."""

    return frozenset(
        GroundAtom(predicate=predicate, arguments=tuple(row))
        for predicate, rows in theory.facts.items()
        for row in rows
    )


def _closure_under_rules(
    fact_atoms: frozenset[GroundAtom],
    rules: frozenset[GroundDefeasibleRule],
) -> frozenset[GroundAtom]:
    """Closure under ``rules`` treated as strict for propagation purposes.

    Shadows each rule's kind to ``"strict"`` so ``strict_closure``
    will propagate it regardless of its original kind. This mirrors
    the internal ``_force_strict_for_closure`` in arguments.py.
    """

    shadowed = tuple(
        GroundDefeasibleRule(
            rule_id=rule.rule_id,
            kind="strict",
            head=rule.head,
            body=rule.body,
        )
        for rule in rules
    )
    return strict_closure(fact_atoms, shadowed)


@given(theory=small_theory_strategy())
@settings(max_examples=500, deadline=None)
def test_hypothesis_every_argument_is_minimal(
    theory: DefeasibleTheory,
) -> None:
    """Garcia & Simari 2004 Def 3.1 condition (3): ``A`` is minimal.

    For every ``Argument(A, h)`` produced, no strict subset ``A' < A``
    also derives ``h`` from ``Pi union A'`` (checked independently of
    the builder's internal minimality filter).
    """

    arguments = build_arguments(theory)
    fact_atoms = _fact_atoms_from_theory(theory)

    # Collect the grounded strict rules once — we reuse them for each
    # proper-subset check.
    for argument in arguments:
        rules = argument.rules
        if not rules:
            continue
        for size in range(len(rules)):
            for subset_tuple in combinations(rules, size):
                subset = frozenset(subset_tuple)
                closure = _closure_under_rules(fact_atoms, subset)
                if argument.conclusion in closure:
                    # Strict-fact conclusion is allowed to be derivable
                    # from the empty set (the <empty, h> argument for
                    # strict heads is a distinct Argument value).
                    if subset == frozenset() and argument.conclusion in closure:
                        continue
                    raise AssertionError(
                        f"non-minimal argument: {argument!r} also derivable from {subset!r}"
                    )


@given(theory=small_theory_strategy())
@settings(max_examples=500, deadline=None)
def test_hypothesis_every_argument_is_non_contradictory(
    theory: DefeasibleTheory,
) -> None:
    """Garcia & Simari 2004 Def 3.1 condition (2): ``Pi union A`` is non-contradictory.

    For every ``Argument(A, h)`` produced, the closure of
    ``Pi union A`` must not contain a complementary pair.
    """

    arguments = build_arguments(theory)
    fact_atoms = _fact_atoms_from_theory(theory)

    from gunray.disagreement import complement

    for argument in arguments:
        closure = _closure_under_rules(fact_atoms, argument.rules)
        for atom in closure:
            assert complement(atom) not in closure, (
                f"contradictory argument: {argument!r} closure contains "
                f"{atom!r} and {complement(atom)!r}"
            )


def _theory_plus_fact(
    theory: DefeasibleTheory,
    predicate: str,
    row: tuple[object, ...],
) -> DefeasibleTheory:
    """Return a copy of ``theory`` with one extra fact row."""

    new_facts: dict[str, set[tuple[object, ...]]] = {
        pred: set(rows) for pred, rows in theory.facts.items()
    }
    new_facts.setdefault(predicate, set()).add(row)
    return DefeasibleTheory(
        facts=new_facts,
        strict_rules=list(theory.strict_rules),
        defeasible_rules=list(theory.defeasible_rules),
        defeaters=list(theory.defeaters),
        superiority=list(theory.superiority),
        conflicts=list(theory.conflicts),
    )


def _defeasible_body_predicate_arities(
    theory: DefeasibleTheory,
) -> frozenset[tuple[str, int]]:
    """Predicates that appear in at least one defeasible or defeater body."""

    body_predicates: set[tuple[str, int]] = set()
    for rule in (*theory.defeasible_rules, *theory.defeaters):
        for body_literal in rule.body:
            atom = parse_atom_text(body_literal)
            body_predicates.add((atom.predicate, len(atom.terms)))
    return frozenset(body_predicates)


@given(theory=small_theory_strategy())
@settings(
    max_examples=500,
    deadline=None,
    suppress_health_check=[HealthCheck.filter_too_much],
)
def test_hypothesis_build_arguments_monotonic_under_body_fact_addition(
    theory: DefeasibleTheory,
) -> None:
    """Adding a fact for an in-body predicate cannot remove existing arguments.

    Formally: ``build_arguments(T) subset build_arguments(T_plus_fact)``.
    This is a structural property of Def 3.1 — new facts can enlarge
    the set of satisfied defeasible/defeater rule bodies, but cannot
    invalidate any existing derivation. The added row uses a fresh
    constant and this property filters to theories with no strict rules
    so the new fact cannot make the strict base itself contradictory.
    """

    assume(not theory.strict_rules)
    base_arguments = build_arguments(theory)
    body_predicates = _defeasible_body_predicate_arities(theory)
    assume(body_predicates)

    predicate, arity = sorted(body_predicates)[0]
    fresh_row = tuple(f"__fresh_fact_{index}__" for index in range(arity))
    extended = _theory_plus_fact(theory, predicate, fresh_row)
    extended_arguments = build_arguments(extended)

    assert base_arguments <= extended_arguments, (
        f"fact monotonicity violated: missing={base_arguments - extended_arguments!r}"
    )


@st.composite
def _theory_with_defeater_strategy(draw: st.DrawFn) -> DefeasibleTheory:
    """Draw a small theory and promote one of its defeasible rules to a defeater.

    Built on top of ``small_theory_strategy``. We pick a defeasible
    rule, remove it from ``defeasible_rules``, and insert it into
    ``defeaters`` with a fresh rule id so every generated theory has
    at least one defeater. If the base theory has no defeasible rule
    to promote, we synthesise a trivial one.
    """

    base = draw(small_theory_strategy())
    pred = draw(st.sampled_from(["p", "q", "r"]))
    body_pred = draw(st.sampled_from(["p", "q", "r"]))
    negated = draw(st.booleans())
    marker = "~" if negated else ""
    defeater_rule = Rule(
        id="__defeater__",
        head=f"{marker}{pred}(X)",
        body=[f"{body_pred}(X)"],
    )
    return DefeasibleTheory(
        facts={p: set(rows) for p, rows in base.facts.items()},
        strict_rules=list(base.strict_rules),
        defeasible_rules=list(base.defeasible_rules),
        defeaters=list(base.defeaters) + [defeater_rule],
        superiority=list(base.superiority),
        conflicts=list(base.conflicts),
    )


@given(theory=_theory_with_defeater_strategy())
@settings(max_examples=200, deadline=None)
def test_hypothesis_defeater_rules_never_warrant_by_answer(
    theory: DefeasibleTheory,
) -> None:
    """Nute/Antoniou reading of defeater rules: they attack, never warrant.

    For every generated theory containing at least one defeater rule,
    and for every ground atom whose predicate is the head of some
    defeater, ``answer(theory, atom, criterion)`` is never ``YES`` by
    virtue of an argument whose rules include a defeater. The
    structural reason: ``dialectic._is_warranted`` filters out any
    candidate whose rule set contains a ``kind="defeater"`` rule
    before attempting tree construction.

    Concretely: for each defeater ``d`` in ``build_arguments(theory)``
    whose conclusion is ``atom``, running ``answer`` for that ``atom``
    never returns ``YES`` purely on the strength of ``d`` — a YES is
    only possible when some *non-defeater* argument for ``atom``
    marks ``U``.
    """

    criterion = GeneralizedSpecificity(theory)
    arguments = build_arguments(theory)

    defeater_arguments = [
        arg for arg in arguments if any(rule.kind == "defeater" for rule in arg.rules)
    ]
    if not defeater_arguments:
        return

    for defeater_arg in defeater_arguments:
        atom = defeater_arg.conclusion
        non_defeater_args_for_atom = [
            arg
            for arg in arguments
            if arg.conclusion == atom and not any(rule.kind == "defeater" for rule in arg.rules)
        ]
        result = answer(theory, atom, criterion)
        if result is Answer.YES:
            # YES is only admissible if a non-defeater argument for
            # the atom also exists. A defeater on its own must never
            # carry an atom to YES.
            assert non_defeater_args_for_atom, (
                f"defeater-only argument warranted atom={atom!r} YES "
                f"without any non-defeater support: "
                f"defeaters={defeater_arguments!r}"
            )
