"""Dialectical machinery: Garcia & Simari 2004 Defs 3.4, 4.1, 4.2, 4.7, 5.1; Proc 5.1.

This module implements the defeat relation and dialectical tree
construction from Garcia & Simari 2004. The public surface here is:

- ``counter_argues`` (Def 3.4) — one argument counter-argues another
  at a literal ``h`` iff ``h`` is (or can be built as) the conclusion
  of a *sub-argument* of the target and the attacker's conclusion
  disagrees with it. **Critical**: the attack must descend into
  sub-arguments, not merely inspect the target's root conclusion.
- ``proper_defeater`` (Def 4.1) / ``blocking_defeater`` (Def 4.2) —
  defeat relations parameterised by a ``PreferenceCriterion``.
- ``DialecticalNode`` (Def 5.1) — immutable tree node.
- ``build_tree`` (Def 5.1 + Def 4.7 acceptable-line conditions) —
  constructs the dialectical tree rooted at an argument, admitting
  children only if the extended line satisfies every Def 4.7
  condition.
- ``mark`` (Proc 5.1) — pure post-order marking on the immutable
  tree. Leaves ``→ U``; any ``U`` child ``→ D``; all ``D`` children
  ``→ U`` (reinstatement).
- ``render_tree`` — pure deterministic Unicode debugger for a
  ``DialecticalNode``. Not a paper definition; a deliberate
  engineering promotion per the B1.5 refactor plan so the renderer
  can visually diagnose Def 4.7 acceptable-line bugs during B1.6.
- ``answer`` (Def 5.3) — four-valued warrant query: ``YES`` if
  ``literal`` is warranted (some argument for ``literal`` roots a
  tree marked ``U``), ``NO`` if its complement is warranted,
  ``UNDECIDED`` if neither is warranted but at least one argument
  exists for ``literal`` or its complement, ``UNKNOWN`` if
  ``literal``'s predicate does not appear in the theory's language.

Explicitly **not** in this module: wiring to ``DefeasibleEvaluator``
— that lands in B1.6. Caching, pruning, or any other optimisation is
also out of scope (Block 1 is correctness-first).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ._internal import _atom_sort_key, _force_strict_for_closure, _ground_theory
from .answer import Answer
from .arguments import (
    Argument,
    build_arguments,
    is_subargument,
)
from .disagreement import complement, disagrees, has_contradiction, strict_closure
from .parser import parse_defeasible_theory
from .preference import PreferenceCriterion
from .schema import DefeasibleTheory
from .types import GroundAtom, GroundDefeasibleRule

DefeaterKind = Literal["proper", "blocking"]
NodeDefeaterKind = Literal["root", "proper", "blocking"]


def _theory_strict_rules(
    theory: DefeasibleTheory,
) -> tuple[GroundDefeasibleRule, ...]:
    """Return the ground strict rules of ``theory`` for disagreement checks.

    Garcia & Simari 2004 Def 3.3 defines disagreement relative to the
    strict knowledge base ``Π``. We reach ``Π`` by re-running the
    argument builder's grounding pass over ``theory``.
    """
    return _ground_theory(theory).grounded_strict_rules


def _theory_pi_facts(theory: DefeasibleTheory) -> frozenset[GroundAtom]:
    """Return the ground facts in ``Pi`` for disagreement checks."""

    return _ground_theory(theory).fact_atoms


@dataclass(frozen=True, slots=True)
class DialecticalContext:
    strict_rules: tuple[GroundDefeasibleRule, ...]
    facts: frozenset[GroundAtom]
    conflicts: frozenset[tuple[str, str]]


def _dialectical_context(theory: DefeasibleTheory) -> DialecticalContext:
    grounded = _ground_theory(theory)
    return DialecticalContext(
        strict_rules=grounded.grounded_strict_rules,
        facts=grounded.fact_atoms,
        conflicts=grounded.conflicts,
    )


def counter_argues(
    attacker: Argument,
    target: Argument,
    theory: DefeasibleTheory,
    *,
    universe: tuple[Argument, ...] | frozenset[Argument] | None = None,
) -> bool:
    """Garcia & Simari 2004 Definition 3.4.

    ``⟨A₁, h₁⟩`` counter-argues ``⟨A₂, h₂⟩`` at literal ``h`` iff
    there exists a sub-argument ``⟨A, h⟩`` of ``⟨A₂, h₂⟩`` such that
    ``h₁`` and ``h`` disagree.

    **Directional fix**: this implementation iterates *every*
    sub-argument of ``target`` (via ``is_subargument`` per
    ``arguments.py``) rather than comparing only root conclusions.
    The old atom-level blocking check never descended into
    sub-arguments; descending is the whole point of this refactor.
    """
    universe = universe if universe is not None else build_arguments(theory)
    context = _dialectical_context(theory)
    for _sub in _disagreeing_subarguments(
        attacker,
        target,
        universe,
        context.strict_rules,
        context.facts,
        context.conflicts,
    ):
        return True
    return False


def _disagreeing_subarguments(
    attacker: Argument,
    target: Argument,
    universe: tuple[Argument, ...] | frozenset[Argument],
    strict_rules: tuple[GroundDefeasibleRule, ...],
    facts: frozenset[GroundAtom],
    conflicts: frozenset[tuple[str, str]] = frozenset(),
) -> list[Argument]:
    """Return every sub-argument ``⟨A, h⟩`` of ``target`` whose
    conclusion disagrees with ``attacker.conclusion``.

    Helper for ``counter_argues`` / ``proper_defeater`` /
    ``blocking_defeater``. Garcia & Simari 2004 Def 3.4 refers to
    the sub-argument at which the counter-attack lands; Defs 4.1 and
    4.2 condition on the preference between the attacker and *that*
    sub-argument, not the root of ``target``.
    """
    hits: list[Argument] = []
    for sub in universe:
        if not is_subargument(sub, target):
            continue
        if disagrees(
            attacker.conclusion,
            sub.conclusion,
            strict_rules,
            facts=facts,
            conflicts=conflicts,
        ):
            hits.append(sub)
    return hits


def proper_defeater(
    attacker: Argument,
    target: Argument,
    criterion: PreferenceCriterion,
    theory: DefeasibleTheory,
    *,
    universe: tuple[Argument, ...] | frozenset[Argument] | None = None,
) -> bool:
    """Garcia & Simari 2004 Definition 4.1.

    ``a1`` is a proper defeater for ``a2`` iff it counter-argues
    ``a2`` at some sub-argument ``⟨A, h⟩`` of ``a2`` AND
    ``criterion`` strictly prefers ``a1`` over ``⟨A, h⟩``.

    Under ``TrivialPreference`` nothing is strictly preferred so
    nothing is proper.
    """
    universe = universe if universe is not None else build_arguments(theory)
    context = _dialectical_context(theory)
    for sub in _disagreeing_subarguments(
        attacker,
        target,
        universe,
        context.strict_rules,
        context.facts,
        context.conflicts,
    ):
        if criterion.prefers(attacker, sub):
            return True
    return False


def blocking_defeater(
    attacker: Argument,
    target: Argument,
    criterion: PreferenceCriterion,
    theory: DefeasibleTheory,
    *,
    universe: tuple[Argument, ...] | frozenset[Argument] | None = None,
) -> bool:
    """Garcia & Simari 2004 Definition 4.2.

    ``a1`` is a blocking defeater for ``a2`` iff it counter-argues
    ``a2`` at some sub-argument ``⟨A, h⟩`` of ``a2`` AND ``criterion``
    prefers neither direction (neither ``a1 > ⟨A, h⟩`` nor
    ``⟨A, h⟩ > a1``).
    """
    universe = universe if universe is not None else build_arguments(theory)
    context = _dialectical_context(theory)
    for sub in _disagreeing_subarguments(
        attacker,
        target,
        universe,
        context.strict_rules,
        context.facts,
        context.conflicts,
    ):
        if not criterion.prefers(attacker, sub) and not criterion.prefers(sub, attacker):
            return True
    return False


@dataclass(frozen=True, slots=True)
class DialecticalNode:
    """Garcia & Simari 2004 Definition 5.1 — node of a dialectical tree.

    Immutable. No ``mark`` field — marking is a pure function over
    the tree (``mark``), per Procedure 5.1. ``defeater_kind`` records
    the Garcia & Simari 2004 p. 110 Def 4.1/4.2 edge kind that
    attached the node to its parent; the root has no incoming
    defeat edge and uses ``"root"``.
    """

    argument: Argument
    children: tuple["DialecticalNode", ...]
    defeater_kind: NodeDefeaterKind = "root"


def _concordant(
    rule_sets: list[frozenset[GroundDefeasibleRule]],
    theory: DefeasibleTheory,
) -> bool:
    """Return True iff ``Π ∪ (union of rule_sets)`` is non-contradictory.

    Garcia & Simari 2004 Def 4.7 cond 2: the supporting and
    interfering sets must each be concordant. Concordance means
    that the union of an argument set's defeasible rules with the
    strict knowledge base ``Π`` produces no pair of complementary
    literals when closed under the rules.

    Implementation reuses ``arguments._force_strict_for_closure`` to
    wrap every defeasible rule as a strict-kind shadow for the
    closure pass, matching the Def 3.1 condition (2) treatment in
    ``build_arguments``.
    """
    context = _dialectical_context(theory)
    rules = frozenset(rule for rule_set in rule_sets for rule in rule_set)
    return _concordant_rules(rules, context.strict_rules, context.facts, context.conflicts, {})


def _concordant_rules(
    rules: frozenset[GroundDefeasibleRule],
    strict_rules: tuple[GroundDefeasibleRule, ...],
    facts: frozenset[GroundAtom],
    conflicts: frozenset[tuple[str, str]],
    cache: dict[frozenset[GroundDefeasibleRule], bool],
) -> bool:
    cached = cache.get(rules)
    if cached is not None:
        return cached
    combined: list[GroundDefeasibleRule] = list(strict_rules)
    for rule in rules:
        combined.append(_force_strict_for_closure(rule))
    closure = strict_closure(frozenset(), tuple(combined), facts=facts)
    if has_contradiction(closure, conflicts=conflicts):
        cache[rules] = False
        return False
    cache[rules] = True
    return True


def _defeat_kind(
    attacker: Argument,
    target: Argument,
    criterion: PreferenceCriterion,
    universe: tuple[Argument, ...] | frozenset[Argument],
    strict_rules: tuple[GroundDefeasibleRule, ...],
    facts: frozenset[GroundAtom],
    conflicts: frozenset[tuple[str, str]],
) -> DefeaterKind | None:
    """Return ``"proper"``, ``"blocking"``, or ``None``.

    Helper used by ``build_tree`` to classify a candidate defeater.
    Proper takes precedence if some disagreeing sub-argument is
    strictly out-preferred by ``attacker``; blocking is returned if
    some disagreeing sub-argument is preference-neutral vs.
    ``attacker``; otherwise ``None``.
    """
    subs = _disagreeing_subarguments(attacker, target, universe, strict_rules, facts, conflicts)
    proper_hit = False
    blocking_hit = False
    for sub in subs:
        if criterion.prefers(attacker, sub):
            proper_hit = True
        elif not criterion.prefers(sub, attacker):
            blocking_hit = True
    if proper_hit:
        return "proper"
    if blocking_hit:
        return "blocking"
    return None


def classify_defeat(
    attacker: Argument,
    target: Argument,
    criterion: PreferenceCriterion,
    theory: DefeasibleTheory,
    *,
    universe: tuple[Argument, ...] | frozenset[Argument] | None = None,
) -> DefeaterKind | None:
    """Classify a candidate defeat as proper, blocking, or absent.

    Garcia & Simari 2004 p. 110 Def 4.1 names proper defeaters and
    Def 4.2 names blocking defeaters. This public helper exposes that
    paper-level distinction for explanation and downstream storage
    layers while delegating to the same classifier used by
    ``build_tree``.
    """

    actual_universe = universe if universe is not None else build_arguments(theory)
    context = _dialectical_context(theory)
    kind = _defeat_kind(
        attacker,
        target,
        criterion,
        actual_universe,
        context.strict_rules,
        context.facts,
        context.conflicts,
    )
    if kind == "proper" or kind == "blocking":
        return kind
    return None


def build_tree(
    root: Argument,
    criterion: PreferenceCriterion,
    theory: DefeasibleTheory,
    *,
    universe: tuple[Argument, ...] | frozenset[Argument] | None = None,
    context: DialecticalContext | None = None,
    concordance_cache: dict[frozenset[GroundDefeasibleRule], bool] | None = None,
) -> DialecticalNode:
    """Garcia & Simari 2004 Def 5.1 + Def 4.7 acceptable argumentation line.

    Construct the dialectical tree rooted at ``root``. A child is
    admitted only if (a) it is a proper or blocking defeater of its
    parent, and (b) extending the current line with it still
    satisfies every Def 4.7 acceptable-line condition:

    1. The line is finite.
    2. The supporting set ``S_s = ⋃ A_{2i}`` (0-indexed: positions 0,
       2, 4, ...) and interfering set ``S_i = ⋃ A_{2i+1}`` (positions
       1, 3, 5, ...) are each concordant (union with ``Π``
       non-contradictory).
    3. No argument in the line is a sub-argument of an earlier one.
    4. If the parent edge was a blocking defeat, the child edge must
       be a proper defeat (otherwise the line terminates).

    Violating conditions 2, 3, or 4 truncates that branch by simply
    not adding the violator as a child. Condition 1 is structurally
    guaranteed: ``build_arguments`` returns a finite frozenset and
    cond 3 forbids re-entry along a line.
    """
    argument_universe = universe if universe is not None else build_arguments(theory)
    actual_context = context if context is not None else _dialectical_context(theory)
    actual_concordance_cache = concordance_cache if concordance_cache is not None else {}
    return _expand(
        root,
        [root],
        [None],
        argument_universe,
        criterion,
        actual_context.strict_rules,
        actual_context.facts,
        actual_context.conflicts,
        root.rules,
        frozenset(),
        actual_concordance_cache,
    )


def _expand(
    current: Argument,
    line: list[Argument],
    edge_kinds: list[DefeaterKind | None],
    universe: tuple[Argument, ...] | frozenset[Argument],
    criterion: PreferenceCriterion,
    strict_rules: tuple[GroundDefeasibleRule, ...],
    facts: frozenset[GroundAtom],
    conflicts: frozenset[tuple[str, str]],
    supporting_rules: frozenset[GroundDefeasibleRule],
    interfering_rules: frozenset[GroundDefeasibleRule],
    concordance_cache: dict[frozenset[GroundDefeasibleRule], bool],
) -> DialecticalNode:
    """Recursive expansion of a single dialectical-tree node.

    ``line[i]`` is the argument at position ``i`` along the path
    from the root to ``current`` (so ``line[-1] == current``).
    ``edge_kinds[i]`` is the kind of defeat (``"proper"`` /
    ``"blocking"`` / ``None`` for the root) used to attach
    ``line[i]`` to its parent.
    """
    children_nodes: list[DialecticalNode] = []
    parent_edge_kind = edge_kinds[-1]
    node_defeater_kind: NodeDefeaterKind = parent_edge_kind if parent_edge_kind else "root"

    for candidate in universe:
        kind = _defeat_kind(candidate, current, criterion, universe, strict_rules, facts, conflicts)
        if kind is None:
            continue

        # Def 4.7 cond 4: blocking-defeater-of-blocking-defeater
        # terminates the line.
        if parent_edge_kind == "blocking" and kind == "blocking":
            continue

        # Def 4.7 cond 3: no argument in the line is a sub-argument
        # of an earlier one. We only need to check `candidate`
        # against existing line members — earlier inclusions were
        # already checked when they were added.
        if any(is_subargument(candidate, earlier) for earlier in line):
            continue

        # Def 4.7 cond 2: the supporting set S_s (0-indexed even
        # positions) and interfering set S_i (0-indexed odd
        # positions) must each remain concordant with `candidate`
        # added to its appropriate set.
        new_index = len(line)  # position of `candidate` if admitted
        if new_index % 2 == 0:
            next_supporting_rules = supporting_rules | candidate.rules
            next_interfering_rules = interfering_rules
            if not _concordant_rules(
                next_supporting_rules,
                strict_rules,
                facts,
                conflicts,
                concordance_cache,
            ):
                continue
        else:
            next_supporting_rules = supporting_rules
            next_interfering_rules = interfering_rules | candidate.rules
            if not _concordant_rules(
                next_interfering_rules,
                strict_rules,
                facts,
                conflicts,
                concordance_cache,
            ):
                continue

        # All Def 4.7 conditions satisfied — recurse.
        new_line = line + [candidate]
        new_edges = edge_kinds + [kind]
        children_nodes.append(
            _expand(
                candidate,
                new_line,
                new_edges,
                universe,
                criterion,
                strict_rules,
                facts,
                conflicts,
                next_supporting_rules,
                next_interfering_rules,
                concordance_cache,
            )
        )

    return DialecticalNode(
        argument=current,
        children=tuple(children_nodes),
        defeater_kind=node_defeater_kind,
    )


def mark(node: DialecticalNode) -> Literal["U", "D"]:
    """Garcia & Simari 2004 Procedure 5.1 — pure marking.

    Post-order:

    - leaf ``→ U``
    - inner node with any ``U`` child ``→ D``
    - inner node whose every child marks ``D`` ``→ U`` (reinstatement)

    No mutation, no caching, no early exit. Block 1 is
    correctness-first.
    """
    return _mark_table(node)[node]


def _format_atom(atom: GroundAtom) -> str:
    """Pretty-print a ground atom for the tree renderer.

    ``atom.predicate`` already carries the ``~`` prefix for strong
    negation (per ``disagreement.complement``). Zero-arity atoms
    render bare; others render as ``pred(a, b, c)``.
    """
    if not atom.arguments:
        return atom.predicate
    args = ", ".join(str(arg) for arg in atom.arguments)
    return f"{atom.predicate}({args})"


def _format_rule_ids(argument: Argument) -> str:
    """Return the sorted rule-id list for an argument's header line."""
    ids = sorted(rule.rule_id for rule in argument.rules)
    return "[" + ", ".join(ids) + "]"


def _sorted_children(node: DialecticalNode) -> tuple[DialecticalNode, ...]:
    """Sort children by their argument's conclusion for stable rendering.

    Uses ``defeasible._atom_sort_key`` as the primary key (by
    ``(predicate, arguments)``) and the sorted rule-id tuple as a
    secondary key to distinguish distinct arguments that share a
    conclusion.
    """
    return tuple(
        sorted(
            node.children,
            key=lambda child: (
                _atom_sort_key(child.argument.conclusion),
                tuple(sorted(rule.rule_id for rule in child.argument.rules)),
            ),
        )
    )


def render_tree(node: DialecticalNode) -> str:
    """Render ``node`` as a deterministic Unicode tree.

    Format::

        conclusion  [rule_id, rule_id, ...]  (U|D)
        ├─ child_conclusion  [...]  (U|D)
        │  └─ ...
        └─ last_child  [...]  (U|D)

    The function is pure and deterministic: given the same input it
    always produces byte-identical output. Children are sorted via
    ``defeasible._atom_sort_key`` on their conclusion, with the
    sorted rule-id tuple as a tiebreaker for distinct arguments
    sharing a conclusion.
    """
    marks = _mark_table(node)
    return "\n".join(_render_lines(node, marks))


def _mark_table(node: DialecticalNode) -> dict[DialecticalNode, Literal["U", "D"]]:
    marks: dict[DialecticalNode, Literal["U", "D"]] = {}

    def visit(current: DialecticalNode) -> Literal["U", "D"]:
        cached = marks.get(current)
        if cached is not None:
            return cached
        if not current.children:
            value: Literal["U", "D"] = "U"
        else:
            child_marks = tuple(visit(child) for child in current.children)
            value = "D" if "U" in child_marks else "U"
        marks[current] = value
        return value

    visit(node)
    return marks


def _render_lines(
    node: DialecticalNode,
    marks: dict[DialecticalNode, Literal["U", "D"]],
) -> list[str]:
    """Return the rendered lines for ``node`` and its descendants.

    The header line is rendered without any prefix; caller-supplied
    indentation is handled by ``_render_child_lines`` for nested
    subtrees.
    """
    head = (
        f"{_format_atom(node.argument.conclusion)}  "
        f"{_format_rule_ids(node.argument)}  ({marks[node]})"
    )
    lines = [head]
    children = _sorted_children(node)
    for index, child in enumerate(children):
        is_last = index == len(children) - 1
        lines.extend(_render_child_lines(child, is_last, marks))
    return lines


def _render_child_lines(
    child: DialecticalNode,
    is_last: bool,
    marks: dict[DialecticalNode, Literal["U", "D"]],
) -> list[str]:
    """Render ``child``'s subtree with tree-drawing prefixes."""
    branch = "└─ " if is_last else "├─ "
    continuation = "   " if is_last else "│  "
    child_lines = _render_lines(child, marks)
    rendered = [branch + child_lines[0]]
    for line in child_lines[1:]:
        rendered.append(continuation + line)
    return rendered


def render_tree_mermaid(tree: DialecticalNode) -> str:
    """Render ``tree`` as GitHub-native Mermaid flowchart source.

    Pure deterministic output formatter — no semantic risk. The
    emitted Mermaid uses a ``flowchart TD`` (top-down) layout. Each
    :class:`DialecticalNode` produces a single node line of the form
    ``nK["conclusion [rule_ids] U|D"]`` and each parent→child
    relation produces an edge line ``nI --> nJ``. Synthetic node ids
    (``n0``, ``n1``, ...) are assigned via pre-order traversal using
    :func:`_sorted_children`, so output is byte-stable for any tree.

    U/D marks come from :func:`_mark_table`; the conclusion is
    formatted with :func:`_format_atom` and the rule list with
    :func:`_format_rule_ids` so the Mermaid label matches
    :func:`render_tree` semantics modulo layout.
    """
    marks = _mark_table(tree)
    lines: list[str] = ["flowchart TD"]
    ids: dict[int, str] = {}
    edges: list[str] = []

    def visit(node: DialecticalNode) -> None:
        node_id = f"n{len(ids)}"
        ids[id(node)] = node_id
        label = (
            f"{_format_atom(node.argument.conclusion)} "
            f"{_format_rule_ids(node.argument)} "
            f"{marks[node]}"
        )
        lines.append(f'    {node_id}["{label}"]')
        children = _sorted_children(node)
        child_ids: list[str] = []
        for child in children:
            visit(child)
            child_ids.append(ids[id(child)])
        for child_id in child_ids:
            edges.append(f"    {node_id} --> {child_id}")

    visit(tree)
    lines.extend(edges)
    return "\n".join(lines)


def _format_antecedents(argument: Argument) -> str:
    """Return a brace-delimited list of an argument's rule bodies.

    Used by :func:`explain` when describing what an argument is
    ``from``. Matches Garcia & Simari 2004 §6 reader-facing prose:
    an argument is characterised by the antecedents that ground its
    derivation. Strict-only arguments (empty ``rules``) render as
    ``{}``.
    """

    antecedents: set[GroundAtom] = set()
    for rule in argument.rules:
        for atom in rule.body:
            antecedents.add(atom)
    sorted_atoms = sorted(antecedents, key=_atom_sort_key)
    return "{" + ", ".join(_format_atom(atom) for atom in sorted_atoms) + "}"


def explain(
    tree: DialecticalNode,
    criterion: PreferenceCriterion,
) -> str:
    """Render a dialectical tree as prose, citing Garcia & Simari 2004 §6.

    Garcia & Simari 2004 §6 ("Explaining answers") describes DeLP's
    obligation to justify every answer: for a query ``h``, the
    system must identify the argument that supports ``h`` and the
    dialectical analysis that either warrants it or defeats it. This
    helper walks the *already-marked* tree top-down and produces a
    prose transcript of that analysis.

    The first line names the root conclusion and its four-valued
    verdict at the root: ``YES`` if the root marks ``U``, ``NO``
    otherwise (``D``). Each node below reports its conclusion,
    antecedent set, rule ids, and — for non-root nodes — the
    preference reason ``criterion.explain_preference`` returns for
    its victory over its parent (or, when the parent mark is ``U``
    and the child's mark is ``D``, the reverse direction).

    Reuses :func:`_mark_table` and :func:`_sorted_children` so the
    output is deterministic and consistent with :func:`render_tree`.

    Parameters
    ----------
    tree
        A ``DialecticalNode`` as returned by :func:`build_tree`.
    criterion
        The preference criterion that was used to build ``tree``.
        Needed to produce the "why-prefer" reason on each edge.

    Returns
    -------
    str
        A multi-line prose explanation, without a trailing newline.
    """

    marks = _mark_table(tree)
    root_mark = marks[tree]
    verdict = "YES" if root_mark == "U" else "NO"
    root_conclusion = _format_atom(tree.argument.conclusion)
    root_ants = _format_antecedents(tree.argument)
    root_rules = ", ".join(sorted(rule.rule_id for rule in tree.argument.rules))
    lines: list[str] = [
        f"{root_conclusion} is {verdict}.",
        f"An argument supports {root_conclusion} from {root_ants} via {root_rules}.",
    ]
    for child in _sorted_children(tree):
        lines.extend(_explain_child_lines(child, tree, criterion, marks))
    return "\n".join(lines)


def _explain_child_lines(
    child: DialecticalNode,
    parent: DialecticalNode,
    criterion: PreferenceCriterion,
    marks: dict[DialecticalNode, Literal["U", "D"]],
) -> list[str]:
    """Return the prose lines describing ``child``'s defeat of ``parent``.

    Walks ``child``'s subtree recursively. The verb depends on
    relative marks: a ``U`` child defeats its parent (which marks
    ``D``); a ``D`` child failed to defeat its parent (which marks
    ``U``). The preference-reason clause is drawn from
    ``criterion.explain_preference`` in the appropriate direction,
    with a blocking-defeat fallback when neither direction is
    strictly preferred.
    """

    child_mark = marks[child]
    child_conclusion = _format_atom(child.argument.conclusion)
    child_ants = _format_antecedents(child.argument)
    child_rules = ", ".join(sorted(rule.rule_id for rule in child.argument.rules))

    if child_mark == "U":
        # Child wins over parent. Garcia & Simari 2004 §6: the reason
        # is the preference ``criterion`` awards the child over the
        # parent. Under blocking defeat neither side is strictly
        # preferred; we say so explicitly.
        reason = criterion.explain_preference(child.argument, parent.argument)
        clause = (
            f"which is {reason}"
            if reason is not None
            else "which is a blocking defeater (neither side strictly preferred)"
        )
        head = (
            f"It is defeated by an argument for {child_conclusion} "
            f"from {child_ants} via {child_rules}, {clause}."
        )
    else:
        # Child failed to defeat parent — either it was itself
        # defeated by a grandchild (reinstatement, Proc 5.1) or it
        # was strictly out-preferred at construction time but still
        # admitted because it counter-argued. We report the
        # reinstatement narrative; the tree structure carries the
        # detail on why.
        reason_parent_wins = criterion.explain_preference(parent.argument, child.argument)
        if reason_parent_wins is not None:
            clause = f"but the parent is {reason_parent_wins}"
        else:
            clause = "but it is itself defeated further down"
        head = (
            f"An attacker for {child_conclusion} from {child_ants} "
            f"via {child_rules} was considered, {clause}."
        )

    lines = [head]
    for grandchild in _sorted_children(child):
        lines.extend(_explain_child_lines(grandchild, child, criterion, marks))
    return lines


def _theory_predicates(theory: DefeasibleTheory) -> frozenset[str]:
    """Return the set of predicate names appearing in ``theory``'s language.

    Garcia & Simari 2004 Def 5.3 UNKNOWN case: a literal ``h`` whose
    predicate does not appear in the language of the program returns
    ``UNKNOWN``. The language is the set of predicates mentioned in
    the facts and in the heads and bodies of strict rules, defeasible
    rules, and defeaters. Strong-negation prefixes are stripped so
    ``p`` and ``~p`` live in the same language cell.
    """
    _facts, defeasible_rules, _conflicts = parse_defeasible_theory(theory)
    predicates: set[str] = set(theory.facts.keys())
    for rule in defeasible_rules:
        predicates.add(_strip_negation(rule.head.predicate))
        for atom in rule.body:
            predicates.add(_strip_negation(atom.predicate))
    return frozenset(predicates)


def _strip_negation(predicate: str) -> str:
    """Return ``predicate`` with its strong-negation ``~`` prefix removed."""
    if predicate.startswith("~"):
        return predicate[1:]
    return predicate


def _is_warranted(
    literal: GroundAtom,
    arguments: frozenset[Argument],
    criterion: PreferenceCriterion,
    theory: DefeasibleTheory,
) -> bool:
    """Return True iff some ``⟨A, literal⟩`` has a tree that marks ``U``.

    Garcia & Simari 2004 Def 5.3: ``literal`` is *warranted* iff
    there exists an argument for it whose dialectical tree
    (Def 5.1 + Def 4.7) is marked ``U`` at the root under
    Procedure 5.1.

    **Defeater-kind filter** (Nute/Antoniou reading, see
    ``notes/b2_defeater_participation.md``). Gunray enumerates a
    one-rule argument ``<{d}, head(d)>`` for each grounded defeater
    so it can attack defeasible arguments in the dialectical tree.
    Such an argument must never itself warrant a query, so we skip
    any candidate whose rule set contains a defeater-kind rule when
    testing warrant.
    """
    for arg in arguments:
        if arg.conclusion != literal:
            continue
        if any(rule.kind == "defeater" for rule in arg.rules):
            continue
        tree = build_tree(arg, criterion, theory, universe=arguments)
        if mark(tree) == "U":
            return True
    return False


def answer(
    theory: DefeasibleTheory,
    literal: GroundAtom,
    criterion: PreferenceCriterion,
) -> Answer:
    """Garcia & Simari 2004 Definition 5.3 — four-valued DeLP answer.

    - ``YES`` if ``literal`` is warranted from ``theory`` (there
      exists an argument ``⟨A, literal⟩`` whose marked dialectical
      tree has root ``U``).
    - ``NO`` if ``complement(literal)`` is warranted.
    - ``UNDECIDED`` if neither is warranted but at least one
      argument exists for ``literal`` or its complement.
    - ``UNKNOWN`` if the predicate of ``literal`` (with strong
      negation stripped) does not appear in the language of
      ``theory``.

    Under ``TrivialPreference`` (Block 1) nothing is proper, every
    counter-argument is a blocking defeater, and the dialectical
    tree structure together with Procedure 5.1 marking determines
    the answer. Real specificity arrives in Block 2 via
    ``GeneralizedSpecificity``.
    """
    arguments = build_arguments(theory)

    if _is_warranted(literal, arguments, criterion, theory):
        return Answer.YES

    opposite = complement(literal)
    if _is_warranted(opposite, arguments, criterion, theory):
        return Answer.NO

    has_argument_for_either = any(
        arg.conclusion == literal or arg.conclusion == opposite for arg in arguments
    )
    if has_argument_for_either:
        return Answer.UNDECIDED

    predicates = _theory_predicates(theory)
    literal_predicate = _strip_negation(literal.predicate)
    complement_predicate = _strip_negation(opposite.predicate)
    if literal_predicate not in predicates and complement_predicate not in predicates:
        return Answer.UNKNOWN

    return Answer.UNDECIDED
