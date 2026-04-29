from __future__ import annotations

from pathlib import Path


def test_diller_2025_is_load_bearing_and_cited_to_paper_pages() -> None:
    citations = Path("CITATIONS.md").read_text(encoding="utf-8")
    grounding = Path("src/gunray/grounding.py").read_text(encoding="utf-8")

    load_bearing = citations.split("## Contextual", 1)[0]
    assert "Diller" in load_bearing
    assert "Definition 9" in load_bearing
    assert "Algorithm 2" in load_bearing
    assert "page images" not in grounding
    assert "Diller et al. 2025" in grounding
    assert "p. 3" in grounding
    assert "p. 7" in grounding
