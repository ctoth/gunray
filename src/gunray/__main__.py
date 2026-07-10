"""Run the Gunray interactive shell with ``python -m gunray``."""

from .cli import main

raise SystemExit(main(["repl"]))
