"""Project macros for the dashboard YAML."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import tiles  # noqa: E402
from glyf.dashboard.macros import alert, ui  # noqa: E402


def freshness():
    """The "Data as of" banner; a warning once the extract looks stalled (see tiles.yml `meta`)."""
    meta = tiles.one("dashboard_meta")
    note = tiles.freshness_note(meta)
    if meta["days_stale"] > tiles.MANIFEST["meta"]["stale_after_days"]:
        return alert.warning(note, title="Stale data")
    return ui.text(note)
