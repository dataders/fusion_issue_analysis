"""Keep a refreshed Graphene cache parseable, safe to embed, and schema-checked."""

import importlib.util
import json
from pathlib import Path

import duckdb
import pytest

SPEC = importlib.util.spec_from_file_location(
    "graphene_refresh", Path(__file__).resolve().parents[1] / "dashboard/graphene/refresh.py"
)
refresh = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(refresh)


def make_export(tmp_path, sql="select label_name from main.fct_issue_labels"):
    source = tmp_path / "source.duckdb"
    with duckdb.connect(str(source)) as con:
        con.execute("create table dashboard_meta as select date '2026-10-14' as as_of_date")
        con.execute("create table fct_issue_labels (label_name varchar)")
        con.execute("insert into fct_issue_labels values (?)", ["</script><script>unsafe()</script>"])
    payload = {
        "code": refresh.OLD_NOTE + refresh.OLD_CALLOUT + "Value(node_42, { data: 'unassigned', column: 'total' });",
        "data": {"query": {"sql": sql, "fields": [{"name": "label_name"}], "rows": [], "runAt": 0}},
    }
    html = tmp_path / "index.html"
    html.write_text("<script>window.$GRAPHENE_STANDALONE=" + json.dumps(payload) + ";</script><p>unchanged</p>")
    return source, html


def test_refresh_preserves_renderer_and_safely_replaces_results(tmp_path):
    source, html = make_export(tmp_path)
    assert refresh.refresh(source, html) == 1
    rendered = html.read_text()
    payload, _, _ = refresh.extract_payload(rendered)
    assert payload["data"]["query"]["rows"] == [{"label_name": "</script><script>unsafe()</script>"}]
    assert rendered.count("</script>") == 1
    assert rendered.endswith(";</script><p>unchanged</p>")
    assert "Data as of 2026-10-14" in payload["code"]
    assert "open issues are unassigned" not in payload["code"]
    assert "data: 'unassigned'" not in payload["code"]
    assert refresh.refresh(source, html) == 1


@pytest.mark.parametrize("sql", ["delete from fct_issue_labels", "select label_name as renamed from fct_issue_labels"])
def test_refresh_rejects_mutations_and_schema_drift_without_overwriting(tmp_path, sql):
    source, html = make_export(tmp_path, sql)
    before = html.read_text()
    with pytest.raises(ValueError):
        refresh.refresh(source, html)
    assert html.read_text() == before
