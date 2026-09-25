import marimo

__generated_with = "0.23.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import sys
    from pathlib import Path

    import marimo as mo
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go

    # dashboard/tiles.py: the tile contract (tiles.yml) + dbt model reader.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import tiles

    return go, mo, pd, px, tiles


@app.cell
def _(mo, pd, px, tiles):
    CATEGORIES = tiles.categories("issue_category")
    CATEGORY_COLORS = {c: tiles.color("issue_category", c) for c in CATEGORIES}
    CATEGORY_LABELS = {c: tiles.label("issue_category", c) for c in CATEGORIES}

    def frame(tile_id):
        """A tile's model rows, in the order tiles.yml specifies."""
        return pd.DataFrame(tiles.tile_rows(tile_id))

    def heading(tile_id):
        t = tiles.tile(tile_id)
        return mo.md(f"### {t['title']}\n{t.get('subtitle', '')}")

    def style(fig, height=320, hovermode="x unified"):
        fig.update_layout(
            template="plotly_white",
            height=height,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None),
            hovermode=hovermode,
        )
        return fig

    def category_bar(tile_id, y, total):
        """Horizontal bar of issue_count stacked by issue_category, largest total on top."""
        df = frame(tile_id)
        order = list(dict.fromkeys(df[y]))  # order_by sorts by {total} desc
        fig = px.bar(
            df,
            x="issue_count",
            y=y,
            color="issue_category",
            orientation="h",
            category_orders={"issue_category": CATEGORIES, y: order},
            color_discrete_map=CATEGORY_COLORS,
            hover_data={total: True},
            labels={"issue_count": "Open issues", y: "", "issue_category": "Type", total: "Total"},
        )
        fig.for_each_trace(lambda tr: tr.update(name=CATEGORY_LABELS.get(tr.name, tr.name)))
        fig.update_layout(barmode="stack")
        return style(fig, height=max(280, 26 * len(order) + 80), hovermode="closest")

    def link(url):
        return mo.Html(f'<a href="{url}" target="_blank" rel="noopener">open ↗</a>') if url else ""

    def issue_table(tile_id, rename, extra_format=None):
        """Contract columns in contract order, renamed for display, linked to issue_url."""
        t = tiles.tile(tile_id)
        df = frame(tile_id)[t["columns"] + [t["link"]]]
        return mo.ui.table(
            df.rename(columns={**rename, t["link"]: "Link"}),
            selection=None,
            page_size=15,
            show_column_summaries=False,
            format_mapping={
                "Link": link,
                "#": str,  # issue numbers, not quantities: no thousands separator
                "Customer": lambda v: "yes" if v else "",
                **(extra_format or {}),
            },
        )

    return (
        CATEGORIES,
        CATEGORY_COLORS,
        CATEGORY_LABELS,
        category_bar,
        frame,
        heading,
        issue_table,
        style,
    )


@app.cell
def _(mo, tiles):
    _meta = tiles.one(tiles.MANIFEST["meta"]["model"])  # dashboard_meta
    _stale = _meta["days_stale"] > tiles.MANIFEST["meta"]["stale_after_days"]
    _note = tiles.freshness_note(_meta)
    mo.vstack([
        mo.md(f"# {tiles.MANIFEST['title']} · Marimo\n{tiles.MANIFEST['subtitle']}"),
        mo.callout(mo.md(_note), kind="warn") if _stale else mo.md(f"*{_note}*"),
    ])
    return


@app.cell
def _(mo, tiles):
    SECTIONS = {s["id"]: s for s in tiles.sections()}

    def section(section_id):
        return mo.md(f"## {SECTIONS[section_id]['question']}")

    return (section,)


@app.cell
def _(section):
    section("status")
    return


@app.cell
def _(mo, tiles):
    # headline_kpis, formatted per tiles.yml (values, context lines, '—' for nulls)
    mo.hstack(
        [mo.stat(label=k["label"], value=k["value"], caption=k["context"] or None, bordered=True)
         for k in tiles.kpis()],
        wrap=True,
        justify="start",
    )
    return


@app.cell
def _(section):
    section("backlog")
    return


@app.cell
def _(
    CATEGORIES,
    CATEGORY_COLORS,
    CATEGORY_LABELS,
    frame,
    heading,
    mo,
    px,
    style,
):
    _df = frame("backlog_weekly")  # backlog_weekly, long format
    _fig = px.area(
        _df,
        x="week",
        y="open_issues",
        color="issue_category",
        category_orders={"issue_category": CATEGORIES},
        color_discrete_map=CATEGORY_COLORS,
        labels={"week": "Week", "open_issues": "Open issues", "issue_category": "Type"},
    )
    _fig.for_each_trace(lambda tr: tr.update(name=CATEGORY_LABELS.get(tr.name, tr.name)))
    mo.vstack([heading("backlog_weekly"), style(_fig)])
    return


@app.cell
def _(frame, go, heading, mo, style, tiles):
    _df = frame("weekly_flow")  # weekly_flow
    _fig = go.Figure([
        go.Bar(
            x=_df["week"],
            y=_df[_s],
            name=tiles.label("flow", _s),
            marker_color=tiles.color("flow", _s),
            customdata=_df[["net_change"]],
            hovertemplate="%{y} " + _s + " · net change %{customdata[0]:+}<extra></extra>",
        )
        for _s in tiles.tile("weekly_flow")["series"]
    ])
    _fig.update_layout(barmode="group", xaxis_title="Week", yaxis_title="Issues")
    mo.vstack([heading("weekly_flow"), style(_fig)])
    return


@app.cell
def _(section):
    section("triage")
    return


@app.cell
def _(frame, heading, mo, px, style, tiles):
    _df = frame("triage_pipeline")  # sorted by status_order, age_bucket_order
    _fig = px.bar(
        _df,
        x="issue_count",
        y="status_label",
        color="age_bucket",
        orientation="h",
        category_orders={
            "status_label": list(dict.fromkeys(_df["status_label"])),
            "age_bucket": list(dict.fromkeys(_df["age_bucket"])),
        },
        color_discrete_map={b: tiles.color("age_bucket", b) for b in tiles.categories("age_bucket")},
        labels={"issue_count": "Open issues", "status_label": "", "age_bucket": "Age"},
    )
    _fig.update_layout(barmode="stack")
    mo.vstack([heading("triage_pipeline"), style(_fig, height=300, hovermode="closest")])
    return


@app.cell
def _(frame, heading, mo, px, style, tiles):
    _df = frame("response_weekly")  # response_weekly
    _fig = px.line(
        _df,
        x="week",
        y="pct_responded_48h",
        markers=True,
        hover_data=["issues_opened", "responded_48h", "median_hours_to_first_response"],
        labels={
            "week": "Week opened",
            "pct_responded_48h": "% answered within 48h",
            "issues_opened": "Opened",
            "responded_48h": "Answered in 48h",
            "median_hours_to_first_response": "Median hours to first reply",
        },
    )
    _fig.update_traces(line_color=tiles.MANIFEST["palette"]["single_series"])
    _fig.update_yaxes(range=[0, 100], ticksuffix="%")
    mo.vstack([heading("response_weekly"), style(_fig, hovermode="closest")])
    return


@app.cell
def _(heading, issue_table, mo):
    mo.vstack([
        heading("triage_queue"),
        issue_table("triage_queue", {
            "issue_number": "#", "title": "Title", "issue_category": "Type", "age_days": "Age (days)",
            "days_idle": "Idle (days)", "reactions": "Reactions", "comments": "Comments",
            "is_customer_reported": "Customer",
        }),
    ])
    return


@app.cell
def _(section):
    section("where")
    return


@app.cell
def _(category_bar, heading, mo):
    mo.vstack([heading("open_by_area"), category_bar("open_by_area", "area", "area_total")])
    return


@app.cell
def _(category_bar, heading, mo):
    mo.vstack([heading("open_by_adapter"), category_bar("open_by_adapter", "adapter", "adapter_total")])
    return


@app.cell
def _(section):
    section("epics")
    return


@app.cell
def _(heading, issue_table, mo, tiles):
    _bar = tiles.MANIFEST["palette"]["single_series"]

    def _pct_bar(pct):
        if pct is None or pct != pct:
            return "—"
        return mo.Html(
            f'<div style="display:flex;align-items:center;gap:6px;min-width:140px">'
            f'<div style="flex:1;background:#e8e8e6;height:8px;border-radius:4px">'
            f'<div style="width:{pct:.0f}%;background:{_bar};height:8px;border-radius:4px"></div></div>'
            f"<span>{pct:.0f}%</span></div>"
        )

    mo.vstack([
        heading("epic_progress"),  # epic_progress
        issue_table(
            "epic_progress",
            {"epic_number": "#", "title": "Epic", "child_closed": "Closed", "child_total": "Sub-issues",
             "pct_complete": "% complete", "milestone_title": "Milestone"},
            extra_format={"% complete": _pct_bar},
        ),
    ])
    return


@app.cell
def _(section):
    section("next")
    return


@app.cell
def _(heading, issue_table, mo):
    mo.vstack([
        heading("top_requested"),
        issue_table("top_requested", {
            "issue_number": "#", "title": "Title", "issue_category": "Type", "areas": "Areas",
            "triage_status": "Triage", "reactions": "Reactions", "comments": "Comments",
            "age_days": "Age (days)", "is_customer_reported": "Customer",
        }),
    ])
    return


@app.cell
def _(category_bar, heading, mo):
    mo.vstack([heading("assignee_workload"), category_bar("assignee_workload", "assignee_login", "assignee_total")])
    return


if __name__ == "__main__":
    app.run()
