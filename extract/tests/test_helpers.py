"""Unit tests for extract/github/helpers.py — no network required."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from github.helpers import _extract_nested_nodes


def _base_item():
    return {
        "reactions": {"totalCount": 2, "nodes": [{"content": "THUMBS_UP"}]},
        "comments": {
            "totalCount": 1,
            "nodes": [
                {
                    "id": "c1",
                    "reactions": {"totalCount": 0, "nodes": []},
                }
            ],
        },
    }


def test_timeline_items_flattened():
    item = _base_item()
    item["timelineItems"] = {
        "totalCount": 3,
        "nodes": [
            {"__typename": "LabeledEvent", "createdAt": "2024-01-01T00:00:00Z", "label": {"name": "bug"}},
            {"__typename": "LabeledEvent", "createdAt": "2024-01-02T00:00:00Z", "label": {"name": "triage"}},
            {"__typename": "UnlabeledEvent", "createdAt": "2024-01-03T00:00:00Z", "label": {"name": "triage"}},
        ],
    }
    result = _extract_nested_nodes(item)

    assert "timelineItems" not in result, "raw timelineItems key should be removed"
    assert result["timeline_items_totalCount"] == 3
    assert len(result["timeline_items"]) == 3
    assert result["timeline_items"][0]["label"]["name"] == "bug"


def test_no_timeline_items_is_fine():
    """Issues without timelineItems (e.g. old extract runs) should not error."""
    item = _base_item()
    result = _extract_nested_nodes(item)
    assert "timeline_items" not in result
    assert "timeline_items_totalCount" not in result
    assert "timelineItems" not in result


def test_reactions_still_flattened():
    item = _base_item()
    result = _extract_nested_nodes(item)
    assert result["reactions_totalCount"] == 2
    assert isinstance(result["reactions"], list)
    assert result["reactions"][0]["content"] == "THUMBS_UP"


def test_comment_reactions_still_flattened():
    item = _base_item()
    result = _extract_nested_nodes(item)
    comment = result["comments"][0]
    assert comment["reactions_totalCount"] == 0
    assert isinstance(comment["reactions"], list)
