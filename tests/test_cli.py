from __future__ import annotations

import io
import json
import subprocess
import sys

from gunray.cli import GunrayCmd, main, theory_from_data, theory_to_data


def _theory_data() -> dict[str, object]:
    return {
        "facts": {
            "bird": [["opus"]],
            "penguin": [["opus"]],
        },
        "defeasible_rules": [
            {"id": "r1", "head": "flies(X)", "body": ["bird(X)"]},
            {"id": "r2", "head": "~flies(X)", "body": ["penguin(X)"]},
        ],
    }


def test_answer_reads_yaml_and_json_output(tmp_path, capsys) -> None:
    path = tmp_path / "theory.yaml"
    path.write_text(
        """facts:
  bird:
    - [tweety]
defeasible_rules:
  - id: r1
    head: flies(X)
    body: [bird(X)]
""",
        encoding="utf-8",
    )

    exit_code = main(["answer", str(path), 'flies("tweety")', "--format", "json"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == {
        "answer": "yes",
        "literal": {"arguments": ["tweety"], "predicate": "flies"},
    }


def test_tree_text_is_indented_prose_not_box_drawing(tmp_path, capsys) -> None:
    path = tmp_path / "theory.json"
    path.write_text(json.dumps(_theory_data()), encoding="utf-8")

    exit_code = main(["tree", str(path), 'flies("opus")'])

    assert exit_code == 0
    rendered = capsys.readouterr().out
    assert "flies(opus) [r1] (D)" in rendered
    assert "  ~flies(opus) [r2] (U)" in rendered
    assert "├" not in rendered
    assert "└" not in rendered


def test_explain_returns_prose_for_the_selected_tree(tmp_path, capsys) -> None:
    path = tmp_path / "theory.json"
    path.write_text(json.dumps(_theory_data()), encoding="utf-8")

    exit_code = main(["explain", str(path), 'flies("opus")'])

    assert exit_code == 0
    assert "flies(opus) is NO." in capsys.readouterr().out


def test_repl_builds_theory_from_schema_objects() -> None:
    output = io.StringIO()
    repl = GunrayCmd(stdout=output)

    repl.onecmd("clear")
    repl.onecmd('add fact {"predicate": "bird", "arguments": ["tweety"]}')
    repl.onecmd('add defeasible_rules {"id": "r1", "head": "flies(X)", "body": ["bird(X)"]}')
    repl.onecmd('answer flies("tweety")')

    assert "YES" in output.getvalue()


def test_theory_round_trips_the_public_schema_shape() -> None:
    theory = theory_from_data(_theory_data())

    assert theory_from_data(theory_to_data(theory)) == theory


def test_answer_rejects_a_bare_identifier_query(tmp_path, capsys) -> None:
    path = tmp_path / "theory.json"
    path.write_text(json.dumps(_theory_data()), encoding="utf-8")

    exit_code = main(["answer", str(path), "flies(opus)"])

    assert exit_code == 2
    assert "quote string constants" in capsys.readouterr().err


def test_module_entry_point_starts_the_repl() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "gunray"],
        input="exit\n",
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0
    assert "Gunray REPL" in result.stdout
