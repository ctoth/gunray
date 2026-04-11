"""Predicate stratification for negation-as-failure programs."""

from __future__ import annotations

from collections import defaultdict, deque

from .errors import CyclicNegationError
from .types import Rule


def stratify(rules: list[Rule]) -> list[frozenset[str]]:
    """Compute a stratification for a normalized single-head rule set."""

    predicates: set[str] = set()
    positive_edges: dict[str, set[str]] = defaultdict(set)
    negative_edges: dict[str, set[str]] = defaultdict(set)

    for rule in rules:
        head = rule.heads[0]
        head_predicate = head.predicate
        predicates.add(head_predicate)
        for atom in rule.positive_body:
            predicates.add(atom.predicate)
            positive_edges[head_predicate].add(atom.predicate)
        for atom in rule.negative_body:
            predicates.add(atom.predicate)
            negative_edges[head_predicate].add(atom.predicate)

    if not predicates:
        return []

    components = _tarjan_scc(predicates, positive_edges, negative_edges)
    component_index: dict[str, int] = {}
    for index, component in enumerate(components):
        for predicate in component:
            component_index[predicate] = index

    for source, targets in negative_edges.items():
        for target in targets:
            if component_index[source] == component_index[target]:
                raise CyclicNegationError("Program is not stratifiable")

    dag_incoming: dict[int, set[int]] = {index: set() for index in range(len(components))}
    dag_outgoing: dict[int, set[int]] = {index: set() for index in range(len(components))}
    for source, targets in positive_edges.items():
        source_component = component_index[source]
        for target in targets:
            target_component = component_index[target]
            if source_component != target_component:
                dag_outgoing[target_component].add(source_component)
                dag_incoming[source_component].add(target_component)
    for source, targets in negative_edges.items():
        source_component = component_index[source]
        for target in targets:
            target_component = component_index[target]
            if source_component != target_component:
                dag_outgoing[target_component].add(source_component)
                dag_incoming[source_component].add(target_component)

    queue = deque(index for index, incoming in dag_incoming.items() if not incoming)
    order: list[frozenset[str]] = []
    while queue:
        component_id = queue.popleft()
        order.append(frozenset(components[component_id]))
        for downstream in tuple(dag_outgoing[component_id]):
            dag_incoming[downstream].discard(component_id)
            if not dag_incoming[downstream]:
                queue.append(downstream)

    return order


def _tarjan_scc(
    predicates: set[str],
    positive_edges: dict[str, set[str]],
    negative_edges: dict[str, set[str]],
) -> list[set[str]]:
    index_counter = 0
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[set[str]] = []

    def strong_connect(node: str) -> None:
        nonlocal index_counter

        indices[node] = index_counter
        lowlinks[node] = index_counter
        index_counter += 1
        stack.append(node)
        on_stack.add(node)

        neighbors = positive_edges.get(node, set()) | negative_edges.get(node, set())
        for neighbor in neighbors:
            if neighbor not in indices:
                strong_connect(neighbor)
                lowlinks[node] = min(lowlinks[node], lowlinks[neighbor])
            elif neighbor in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[neighbor])

        if lowlinks[node] == indices[node]:
            component: set[str] = set()
            while stack:
                item = stack.pop()
                on_stack.remove(item)
                component.add(item)
                if item == node:
                    break
            components.append(component)

    for predicate in sorted(predicates):
        if predicate not in indices:
            strong_connect(predicate)

    return components
