"""Regression guard for structured ingestion health in the War Room."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WAR_ROOM = ROOT / "frontend" / "src" / "pages" / "WarRoomPage.tsx"


def test_war_room_renders_only_typed_pipeline_statuses() -> None:
    """Structured health metadata must never be enumerated as React children."""
    source = WAR_ROOM.read_text(encoding="utf-8")
    component_block = re.search(
        r"const PIPELINE_COMPONENTS = \[(.*?)\] as const satisfies",
        source,
        re.DOTALL,
    )

    assert component_block is not None
    keys = re.findall(r'key: "([a-z]+)"', component_block.group(1))
    assert keys == [
        "ingestion",
        "correlation",
        "enrichment",
        "detection",
        "alerts",
        "cases",
        "storage",
        "api",
    ]
    assert "Object.entries(health)" not in source
    assert "as string" not in source
    assert "health[component.key]" in source
    assert "ingestionDetails" not in component_block.group(1)
