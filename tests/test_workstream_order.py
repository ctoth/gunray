from __future__ import annotations

import re
from pathlib import Path


def test_paper_png_workstream_dependency_order_is_topological() -> None:
    root = Path(__file__).resolve().parents[1]
    workstream = root / "workstreams" / "gunray-paper-png-workstreams-2026-05-12.md"
    text = workstream.read_text(encoding="utf-8")

    declared = re.findall(r"^\d+\. (WS-GUN-PNG-\d+):", text, flags=re.MULTILINE)
    headings = re.findall(r"^## (WS-GUN-PNG-\d+):", text, flags=re.MULTILINE)

    assert declared == [
        "WS-GUN-PNG-1",
        "WS-GUN-PNG-2",
        "WS-GUN-PNG-3",
        "WS-GUN-PNG-4",
        "WS-GUN-PNG-5",
        "WS-GUN-PNG-6",
    ]
    assert headings == declared
