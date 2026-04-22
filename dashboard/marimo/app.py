import marimo

__generated_with = "0.23.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import duckdb
    import plotly.express as px
    import plotly.graph_objects as go
    import pandas as pd
    import os

    return duckdb, go, mo, os, pd, px


@app.cell
def _(mo):
    mo.md("""
    # dbt-fusion Issue Health · Marimo
    Actionable metrics for dbt-labs/dbt-fusion (excludes EPICs)
    """)
    return


@app.cell
def _(os):
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    DB_PATH = "md:fusion_issues" if os.environ.get("MOTHERDUCK_TOKEN") else os.path.join(PROJECT_ROOT, "data", "fusion_issues.duckdb")
    return (DB_PATH, PROJECT_ROOT)


@app.cell
def _(DB_PATH, PROJECT_ROOT, duckdb):
    def query(sql):
        con = duckdb.connect(DB_PATH, read_only=True)
        if not DB_PATH.startswith("md:"):
            con.execute(f"SET file_search_path = '{PROJECT_ROOT}/transform'")
        df = con.execute(sql).fetchdf()
        con.close()
        return df
    summary = query("SELECT * FROM summary_kpis").iloc[0]
    return query, summary


# ── Key Metrics ────────────────────────────────────────────────────


@app.cell
def _(mo, summary):
    net = int(summary['closed_4w']) - int(summary['opened_4w'])
    sla = summary.get('pct_responded_48h')
    mo.hstack([
        mo.stat(label="Open Issues", value=str(int(summary['open_issues'])), bordered=True),
        mo.stat(label="Net Flow (4 wk)", value=f"{'+' if net >= 0 else ''}{net}", bordered=True),
        mo.stat(label="Median Close (4 wk)", value=str(summary['rolling_median_close_days'] or 'N/A'), bordered=True),
        mo.stat(label="48h Response SLA", value=f"{int(sla)}%" if sla else "N/A", bordered=True),
        mo.stat(label="Stale Issues (30d+)", value=str(int(summary['stale_count'])), bordered=True),
    ])
    return


# ── Cumulative Issue Flow ──────────────────────────────────────────


@app.cell
def _(mo):
    mo.md("## Cumulative Issue Flow")
    return


@app.cell
def _(px, query):
    cum_df = query("SELECT * FROM cumulative_flow")
    fig_cum = px.area(
        cum_df.melt(id_vars='week', value_vars=['cumulative_opened', 'cumulative_closed'],
                    var_name='series', value_name='count'),
        x='week', y='count', color='series',
        color_discrete_map={'cumulative_opened': '#f38ba8', 'cumulative_closed': '#a6e3a1'},
        labels={'series': '', 'count': 'Issues', 'week': 'Week'},
        title='Cumulative Issue Flow',
    )
    fig_cum.update_layout(template='plotly_dark', height=300)
    fig_cum
    return


# ── Velocity & Response ────────────────────────────────────────────


@app.cell
def _(mo):
    mo.md("## Velocity & Response")
    return


@app.cell
def _(px, query):
    vel_df = query("SELECT * FROM velocity")
    fig_vel = px.line(
        vel_df, x='week', y='median_days', color='issue_category',
        color_discrete_map={'bug': '#f38ba8', 'enhancement': '#89b4fa'},
        labels={'issue_category': 'Type', 'median_days': 'Median Days', 'week': 'Week'},
        title='Median Days to Close: Bugs vs Enhancements',
        markers=True,
    )
    fig_vel.update_layout(template='plotly_dark', height=300)
    fig_vel
    return


@app.cell
def _(px, query):
    resp_df = query("SELECT * FROM response_pctiles")
    fig_resp = px.line(
        resp_df.melt(id_vars='week', value_vars=['p25', 'p50', 'p75'],
                     var_name='percentile', value_name='hours'),
        x='week', y='hours', color='percentile',
        color_discrete_map={'p25': '#a6e3a1', 'p50': '#89b4fa', 'p75': '#f38ba8'},
        labels={'percentile': '', 'hours': 'Hours', 'week': 'Week'},
        title='Time to First Response (hours)',
    )
    fig_resp.update_layout(template='plotly_dark', height=300)
    fig_resp
    return


# ── Issue Distribution ─────────────────────────────────────────────


@app.cell
def _(mo):
    mo.md("## Issue Distribution")
    return


@app.cell
def _(px, query):
    age_df = query("SELECT * FROM age_distribution")
    fig_age = px.bar(
        age_df,
        x='age_bucket', y='issue_count', color='issue_category',
        color_discrete_map={'bug': '#f38ba8', 'enhancement': '#89b4fa', 'other': '#a6adc8'},
        category_orders={'age_bucket': ['0-7d', '8-30d', '31-90d', '91-180d', '180d+']},
        labels={'issue_category': 'Type', 'issue_count': 'Issues', 'age_bucket': 'Age'},
        title='Open Issue Age by Type',
        barmode='stack',
    )
    fig_age.update_layout(template='plotly_dark', height=300)
    fig_age
    return


@app.cell
def _(px, query):
    lbl_df = query("SELECT * FROM close_by_label")
    fig_lbl = px.bar(
        lbl_df.sort_values('median_days_to_close'),
        x='median_days_to_close', y='label_name',
        orientation='h',
        labels={'median_days_to_close': 'Median Days', 'label_name': 'Label'},
        title='Median Days to Close by Label',
    )
    fig_lbl.update_layout(template='plotly_dark', height=400)
    fig_lbl
    return


# ── Triage Health ──────────────────────────────────────────────────


@app.cell
def _(mo):
    mo.md("## Triage Health")
    return


@app.cell
def _(mo, query):
    triage = query("SELECT * FROM triage_health").iloc[0]
    mo.hstack([
        mo.stat(label="% Labeled", value=f"{int(triage['pct_labeled'])}%", bordered=True),
        mo.stat(label="% Typed", value=f"{int(triage.get('pct_typed', 0))}%", bordered=True),
        mo.stat(label="% Assigned", value=f"{int(triage['pct_assigned'])}%", bordered=True),
        mo.stat(label="% Milestoned", value=f"{int(triage['pct_milestoned'])}%", bordered=True),
    ])
    return


# ── Workload & Priorities ──────────────────────────────────────────


@app.cell
def _(mo):
    mo.md("## Workload & Priorities")
    return


@app.cell
def _(px, query):
    workload = query("SELECT * FROM assignee_workload")
    fig_wl = px.bar(
        workload.melt(id_vars='assignee_login', value_vars=['bugs', 'enhancements'],
                      var_name='type', value_name='count'),
        x='count', y='assignee_login', color='type',
        color_discrete_map={'bugs': '#f38ba8', 'enhancements': '#89b4fa'},
        orientation='h',
        labels={'type': 'Type', 'count': 'Open Issues', 'assignee_login': 'Assignee'},
        title='Open Issues by Assignee',
        barmode='stack',
    )
    fig_wl.update_layout(template='plotly_dark', height=400, yaxis={'categoryorder': 'total ascending'})
    fig_wl
    return


@app.cell
def _(px, query):
    top = query("SELECT * FROM community_priorities")
    top['label'] = top.apply(lambda r: f"#{r['issue_number']} {r['title'][:45]}", axis=1)
    fig_top = px.bar(
        top, x='reactions_total_count', y='label',
        color='issue_category',
        color_discrete_map={'bug': '#f38ba8', 'enhancement': '#89b4fa', 'other': '#a6adc8'},
        orientation='h',
        labels={'issue_category': 'Type', 'reactions_total_count': 'Reactions', 'label': ''},
        title='Community Priorities',
    )
    fig_top.update_layout(template='plotly_dark', height=500, yaxis={'categoryorder': 'total ascending'})
    fig_top
    return


if __name__ == "__main__":
    app.run()
