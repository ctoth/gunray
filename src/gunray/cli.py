"""Command-line and interactive interfaces for Gunray theories.

The input document is the public ``DefeasibleTheory`` schema encoded as
YAML or JSON. No rule-language syntax is introduced here.
"""

from __future__ import annotations

import argparse
import cmd
import json
import shlex
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TextIO, cast

import yaml

from .adapter import GunrayEvaluator
from .answer import Answer
from .dialectic import explain, render_tree, render_tree_mermaid
from .errors import GunrayError, ParseError
from .parser import parse_atom_text
from .preference import PreferenceCriterion
from .schema import DefeasibleModel, DefeasibleTheory, Rule, Scalar
from .trace import DefeasibleTrace
from .types import Constant, GroundAtom


class CliError(ValueError):
    """Raised for invalid CLI input before it reaches the evaluator."""


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ``gunray`` command and return its process status."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        if args.command == "repl":
            GunrayCmd().cmdloop()
            return 0
        theory = load_theory(args.theory, input_format=args.input_format)
        literal = _parse_ground_literal(args.literal) if hasattr(args, "literal") else None
        result = _run_command(args.command, theory, literal, args.format)
    except (CliError, GunrayError, ParseError, OSError, yaml.YAMLError, ValueError) as exc:
        print(f"gunray: {exc}", file=sys.stderr)
        return 2
    print(result)
    return 0


def load_theory(
    path: str, *, input_format: str = "auto", stdin: TextIO | None = None
) -> DefeasibleTheory:
    """Load the public theory schema from YAML/JSON file input or standard input."""
    text = (stdin or sys.stdin).read() if path == "-" else Path(path).read_text(encoding="utf-8")
    if input_format == "json":
        raw = json.loads(text)
    elif input_format in {"auto", "yaml"}:
        raw = yaml.safe_load(text)
    else:
        raise CliError(f"Unsupported input format: {input_format}")
    return theory_from_data(raw)


def theory_from_data(raw: object) -> DefeasibleTheory:
    """Convert a YAML/JSON document shaped like ``DefeasibleTheory`` into its dataclass."""
    document = _mapping(raw, "theory")
    allowed = {
        "facts",
        "strict_rules",
        "defeasible_rules",
        "defeaters",
        "presumptions",
        "superiority",
        "conflicts",
    }
    unexpected = sorted(set(document) - allowed)
    if unexpected:
        raise CliError(f"Unknown theory fields: {', '.join(unexpected)}")
    return DefeasibleTheory(
        facts=_facts_from_data(document.get("facts", {})),
        strict_rules=_rules_from_data(document.get("strict_rules", []), "strict_rules"),
        defeasible_rules=_rules_from_data(document.get("defeasible_rules", []), "defeasible_rules"),
        defeaters=_rules_from_data(document.get("defeaters", []), "defeaters"),
        presumptions=_rules_from_data(document.get("presumptions", []), "presumptions"),
        superiority=_pairs_from_data(document.get("superiority", []), "superiority"),
        conflicts=_pairs_from_data(document.get("conflicts", []), "conflicts"),
    )


def theory_to_data(theory: DefeasibleTheory) -> dict[str, object]:
    """Return a deterministic YAML/JSON-compatible representation of a theory."""
    return {
        "facts": {
            predicate: [list(row) for row in sorted(rows, key=_row_key)]
            for predicate, rows in sorted(theory.facts.items())
        },
        "strict_rules": [_rule_to_data(rule) for rule in theory.strict_rules],
        "defeasible_rules": [_rule_to_data(rule) for rule in theory.defeasible_rules],
        "defeaters": [_rule_to_data(rule) for rule in theory.defeaters],
        "presumptions": [_rule_to_data(rule) for rule in theory.presumptions],
        "superiority": [list(pair) for pair in theory.superiority],
        "conflicts": [list(pair) for pair in theory.conflicts],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gunray")
    subcommands = parser.add_subparsers(dest="command")
    for name in ("answer", "explain", "tree"):
        command = subcommands.add_parser(name)
        _add_theory_argument(command)
        command.add_argument("literal", help='Ground literal, e.g. flies("tweety")')
        if name == "tree":
            command.add_argument(
                "--format",
                choices=("text", "unicode", "mermaid", "json"),
                default="text",
            )
        else:
            command.add_argument("--format", choices=("text", "json"), default="text")
    model = subcommands.add_parser("model")
    _add_theory_argument(model)
    model.add_argument("--format", choices=("text", "json"), default="text")
    subcommands.add_parser("repl", help="Start an interactive shell")
    return parser


def _add_theory_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("theory", help="YAML/JSON theory file, or - for standard input")
    parser.add_argument("--input-format", choices=("auto", "yaml", "json"), default="auto")


def _run_command(
    command: str,
    theory: DefeasibleTheory,
    literal: GroundAtom | None,
    output_format: str,
) -> str:
    if command == "model":
        model = GunrayEvaluator().evaluate(theory)
        assert isinstance(model, DefeasibleModel)
        return _render_model(model, output_format)
    if literal is None:
        raise CliError(f"{command} requires a literal")
    model, trace = GunrayEvaluator().evaluate_with_trace(theory)
    assert isinstance(model, DefeasibleModel)
    assert isinstance(trace, DefeasibleTrace)
    if command == "answer":
        answer = _answer_from_model(model, literal)
        return _render_answer(answer, literal, output_format)
    tree = trace.trees.get(literal)
    if tree is None:
        raise CliError(f"No argument tree for {_format_atom(literal)}")
    if command == "explain":
        explanation = explain(tree, _criterion_for(theory))
        return _render_explanation(explanation, literal, output_format)
    if command == "tree":
        return _render_tree(tree, output_format)
    raise CliError(f"Unsupported command: {command}")


def _criterion_for(theory: DefeasibleTheory) -> PreferenceCriterion:
    """Use the engine's evaluated tree with its stable public preference composition."""
    from .preference import CompositePreference, GeneralizedSpecificity, SuperiorityPreference

    return CompositePreference(SuperiorityPreference(theory), GeneralizedSpecificity(theory))


def _render_model(model: DefeasibleModel, output_format: str) -> str:
    data = {"sections": _sections_to_data(model.sections)}
    if output_format == "json":
        return _json(data)
    lines: list[str] = []
    for section, predicates in data["sections"].items():
        lines.append(f"{section}:")
        for predicate, rows in cast(dict[str, list[list[Scalar]]], predicates).items():
            lines.append(f"  {predicate}: {json.dumps(rows)}")
    return "\n".join(lines)


def _render_answer(answer: Answer, literal: GroundAtom, output_format: str) -> str:
    if output_format == "json":
        return _json({"answer": answer.value, "literal": _atom_to_data(literal)})
    return answer.name


def _render_explanation(explanation: str, literal: GroundAtom, output_format: str) -> str:
    if output_format == "json":
        return _json({"literal": _atom_to_data(literal), "explanation": explanation})
    return explanation


def _render_tree(tree: object, output_format: str) -> str:
    from .dialectic import DialecticalNode

    node = cast(DialecticalNode, tree)
    if output_format == "unicode":
        return render_tree(node)
    if output_format == "mermaid":
        return render_tree_mermaid(node)
    if output_format == "json":
        return _json(_tree_to_data(node))
    if output_format == "text":
        return "\n".join(_indented_tree_lines(node))
    raise CliError(f"Unsupported tree format: {output_format}")


def _indented_tree_lines(node: object, depth: int = 0) -> list[str]:
    from .dialectic import DialecticalNode, mark

    current = cast(DialecticalNode, node)
    prefix = "  " * depth
    rule_ids = ", ".join(sorted(rule.rule_id for rule in current.argument.rules))
    lines = [f"{prefix}{_format_atom(current.argument.conclusion)} [{rule_ids}] ({mark(current)})"]
    for child in sorted(
        current.children,
        key=lambda item: (_format_atom(item.argument.conclusion), _rule_ids(item)),
    ):
        lines.extend(_indented_tree_lines(child, depth + 1))
    return lines


def _tree_to_data(node: object) -> dict[str, object]:
    from .dialectic import DialecticalNode, mark

    current = cast(DialecticalNode, node)
    children = sorted(
        current.children,
        key=lambda item: (_format_atom(item.argument.conclusion), _rule_ids(item)),
    )
    return {
        "literal": _atom_to_data(current.argument.conclusion),
        "rules": list(_rule_ids(current)),
        "mark": mark(current),
        "children": [_tree_to_data(child) for child in children],
    }


def _answer_from_model(model: DefeasibleModel, literal: GroundAtom) -> Answer:
    row = literal.arguments
    predicate = literal.predicate
    for answer, section in (
        (Answer.YES, "yes"),
        (Answer.NO, "no"),
        (Answer.UNDECIDED, "undecided"),
        (Answer.UNKNOWN, "unknown"),
    ):
        if row in model.sections.get(section, {}).get(predicate, set()):
            return answer
    return Answer.UNKNOWN


def _parse_ground_literal(text: str) -> GroundAtom:
    atom = parse_atom_text(text)
    arguments: list[Scalar] = []
    for term in atom.terms:
        if not isinstance(term, Constant):
            raise CliError("Query literals must be ground; quote string constants")
        arguments.append(term.value)
    return GroundAtom(predicate=atom.predicate, arguments=tuple(arguments))


def _facts_from_data(raw: object) -> dict[str, list[tuple[Scalar, ...]]]:
    facts = _mapping(raw, "facts")
    result: dict[str, list[tuple[Scalar, ...]]] = {}
    for predicate, raw_rows in facts.items():
        if not isinstance(predicate, str):
            raise CliError("Fact predicates must be strings")
        rows = _sequence(raw_rows, f"facts.{predicate}")
        result[predicate] = [_row_from_data(row, f"facts.{predicate}") for row in rows]
    return result


def _rules_from_data(raw: object, section: str) -> tuple[Rule, ...]:
    entries = _sequence(raw, section)
    rules: list[Rule] = []
    for index, entry in enumerate(entries):
        item = _mapping(entry, f"{section}[{index}]")
        if set(item) - {"id", "head", "body"}:
            raise CliError(f"Unknown fields in {section}[{index}]")
        rule_id = _string(item.get("id"), f"{section}[{index}].id")
        head = _string(item.get("head"), f"{section}[{index}].head")
        body = tuple(
            _string(value, f"{section}[{index}].body")
            for value in _sequence(item.get("body", []), f"{section}[{index}].body")
        )
        rules.append(Rule(id=rule_id, head=head, body=body))
    return tuple(rules)


def _pairs_from_data(raw: object, section: str) -> tuple[tuple[str, str], ...]:
    pairs: list[tuple[str, str]] = []
    for index, value in enumerate(_sequence(raw, section)):
        pair = _sequence(value, f"{section}[{index}]")
        if len(pair) != 2:
            raise CliError(f"{section}[{index}] must have exactly two rule ids")
        pairs.append(
            (
                _string(pair[0], f"{section}[{index}][0]"),
                _string(pair[1], f"{section}[{index}][1]"),
            )
        )
    return tuple(pairs)


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise CliError(f"{name} must be a mapping with string keys")
    mapping = cast(dict[object, object], value)
    if not all(isinstance(key, str) for key in mapping):
        raise CliError(f"{name} must be a mapping with string keys")
    return cast(dict[str, object], mapping)


def _sequence(value: object, name: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise CliError(f"{name} must be a list")
    return cast(Sequence[object], value)


def _row_from_data(value: object, name: str) -> tuple[Scalar, ...]:
    row = _sequence(value, name)
    values: list[Scalar] = []
    for item in row:
        if not isinstance(item, (str, int, float, bool)):
            raise CliError(f"{name} rows may contain only string, number, or boolean values")
        values.append(item)
    return tuple(values)


def _string(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise CliError(f"{name} must be a string")
    return value


def _rule_to_data(rule: Rule) -> dict[str, object]:
    return {"id": rule.id, "head": rule.head, "body": list(rule.body)}


def _sections_to_data(
    sections: Mapping[str, Mapping[str, set[tuple[Scalar, ...]]]],
) -> dict[str, object]:
    return {
        section: {
            predicate: [list(row) for row in sorted(rows, key=_row_key)]
            for predicate, rows in sorted(predicates.items())
        }
        for section, predicates in sorted(sections.items())
    }


def _row_key(row: tuple[Scalar, ...]) -> str:
    return json.dumps(row, sort_keys=True, default=str)


def _atom_to_data(atom: GroundAtom) -> dict[str, object]:
    return {"predicate": atom.predicate, "arguments": list(atom.arguments)}


def _format_atom(atom: GroundAtom) -> str:
    return (
        atom.predicate
        if not atom.arguments
        else f"{atom.predicate}({', '.join(map(str, atom.arguments))})"
    )


def _rule_ids(node: object) -> tuple[str, ...]:
    from .dialectic import DialecticalNode

    return tuple(sorted(rule.rule_id for rule in cast(DialecticalNode, node).argument.rules))


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class GunrayCmd(cmd.Cmd):
    """Incremental shell for loading, querying, and editing schema-backed theories."""

    intro = "Gunray REPL. Type help or ? to list commands."
    prompt = "gunray> "

    def __init__(self, *, stdout: TextIO | None = None) -> None:
        super().__init__(stdout=stdout)
        self.theory: DefeasibleTheory | None = None

    def do_load(self, argument: str) -> None:
        """load PATH: Load a YAML or JSON theory document."""
        try:
            self.theory = load_theory(_one_argument(argument, "load PATH"))
        except (CliError, OSError, yaml.YAMLError, ValueError) as exc:
            self._error(exc)

    def do_save(self, argument: str) -> None:
        """save PATH: Save the current theory as YAML."""
        theory = self._require_theory()
        if theory is None:
            return
        try:
            Path(_one_argument(argument, "save PATH")).write_text(
                yaml.safe_dump(theory_to_data(theory), sort_keys=False), encoding="utf-8"
            )
        except (CliError, OSError, yaml.YAMLError) as exc:
            self._error(exc)

    def do_show(self, argument: str) -> None:
        """show [SECTION]: Print the current schema, or one section."""
        theory = self._require_theory()
        if theory is None:
            return
        data = theory_to_data(theory)
        section = argument.strip()
        if section:
            if section not in data:
                self._error(CliError(f"Unknown section: {section}"))
                return
            data = {section: data[section]}
        self._write(yaml.safe_dump(data, sort_keys=False).rstrip())

    def do_answer(self, argument: str) -> None:
        """answer LITERAL: Return the four-valued result for a ground literal."""
        self._query("answer", argument)

    def do_explain(self, argument: str) -> None:
        """explain LITERAL: Explain the selected argument tree."""
        self._query("explain", argument)

    def do_tree(self, argument: str) -> None:
        """tree LITERAL [FORMAT]: Render text, unicode, mermaid, or json."""
        parts = shlex.split(argument)
        if not parts:
            self._error(CliError("Usage: tree LITERAL [FORMAT]"))
            return
        output_format = parts[1] if len(parts) == 2 else "text"
        if len(parts) > 2:
            self._error(CliError("Usage: tree LITERAL [FORMAT]"))
            return
        self._query("tree", parts[0], output_format)

    def do_add(self, argument: str) -> None:
        """add SECTION DATA: Add a fact or structured rule from one YAML/JSON object."""
        theory = self._require_theory()
        if theory is None:
            return
        section, data = _split_section_data(argument, "add SECTION DATA")
        try:
            if section == "fact":
                updated = theory_to_data(theory)
                fact = _mapping(yaml.safe_load(data), "fact")
                predicate = _string(fact.get("predicate"), "fact.predicate")
                row = list(_row_from_data(fact.get("arguments", []), "fact.arguments"))
                facts = cast(dict[str, list[list[Scalar]]], updated["facts"])
                facts.setdefault(predicate, []).append(row)
                self.theory = theory_from_data(updated)
            elif section in {"strict_rules", "defeasible_rules", "defeaters", "presumptions"}:
                updated = theory_to_data(theory)
                rules = cast(list[object], updated[section])
                rules.append(yaml.safe_load(data))
                self.theory = theory_from_data(updated)
            else:
                raise CliError(
                    "add supports fact, strict_rules, defeasible_rules, defeaters, presumptions"
                )
        except (CliError, ValueError, yaml.YAMLError) as exc:
            self._error(exc)

    def do_remove(self, argument: str) -> None:
        """remove RULE_ID: Remove a rule from any rule section."""
        theory = self._require_theory()
        if theory is None:
            return
        rule_id = argument.strip()
        if not rule_id:
            self._error(CliError("Usage: remove RULE_ID"))
            return
        data = theory_to_data(theory)
        removed = False
        for section in ("strict_rules", "defeasible_rules", "defeaters", "presumptions"):
            rules = cast(list[dict[str, object]], data[section])
            remaining = [rule for rule in rules if rule["id"] != rule_id]
            if len(remaining) != len(rules):
                data[section] = remaining
                removed = True
        if not removed:
            self._error(CliError(f"No rule with id {rule_id!r}"))
            return
        try:
            self.theory = theory_from_data(data)
        except ValueError as exc:
            self._error(exc)

    def do_clear(self, argument: str) -> None:
        """clear: Replace the current theory with an empty theory."""
        if argument.strip():
            self._error(CliError("Usage: clear"))
            return
        self.theory = DefeasibleTheory()

    def do_quit(self, argument: str) -> bool:
        """quit: Exit the REPL."""
        return True

    def do_exit(self, argument: str) -> bool:
        """exit: Exit the REPL."""
        return True

    def do_EOF(self, argument: str) -> bool:
        """Exit the REPL on end of input."""
        self._write("")
        return True

    def _query(self, command: str, argument: str, output_format: str = "text") -> None:
        theory = self._require_theory()
        if theory is None:
            return
        try:
            literal = _parse_ground_literal(argument)
            self._write(_run_command(command, theory, literal, output_format))
        except (CliError, GunrayError, ParseError, ValueError) as exc:
            self._error(exc)

    def _require_theory(self) -> DefeasibleTheory | None:
        if self.theory is None:
            self._error(CliError("Load a theory first"))
        return self.theory

    def _error(self, exc: Exception) -> None:
        self._write(f"Error: {exc}")

    def _write(self, value: str) -> None:
        self.stdout.write(value + "\n")


def _one_argument(argument: str, usage: str) -> str:
    parts = shlex.split(argument)
    if len(parts) != 1:
        raise CliError(f"Usage: {usage}")
    return parts[0]


def _split_section_data(argument: str, usage: str) -> tuple[str, str]:
    section, separator, data = argument.partition(" ")
    if not section or not separator or not data.strip():
        raise CliError(f"Usage: {usage}")
    return section, data.strip()


if __name__ == "__main__":
    raise SystemExit(main())
