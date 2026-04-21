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

    return duckdb, mo, px


@app.cell
def _():
    import os
    _QUERIES_DIR = os.path.join(os.path.dirname(__file__), "queries")
    def load_sql(name):
        with open(os.path.join(_QUERIES_DIR, f"{name}.sql")) as f:
            return f.read()

    return (load_sql,)


@app.cell
def _(mo):
    mo.md("""
    # dbt-fusion Issue Health · Marimo
    """)
    return


@app.cell
def _(duckdb, load_sql):
    def query(sql):
        con = duckdb.connect(
            '/Users/dataders/Developer/fusion_issue_analysis/data/fusion_issues.duckdb',
            read_only=True
        )
        con.execute("SET file_search_path = '/Users/dataders/Developer/fusion_issue_analysis/transform'")
        df = con.execute(sql).fetchdf()
        con.close()
        return df

    summary = query(load_sql("summary")).iloc[0]
    return query, summary


@app.cell
def _(mo, summary):
    net = int(summary['closed_4w']) - int(summary['opened_4w'])
    mo.hstack([
        mo.stat(label="Open Issues", value=str(int(summary['open_issues'])), bordered=True),
        mo.stat(label="Net Flow (4 wk)", value=f"{'+' if net>=0 else ''}{net}", bordered=True),
        mo.stat(label="Median Close Days", value=str(summary['median_close_days'] or 'N/A'), bordered=True),
        mo.stat(label="Stale Issues", value=str(int(summary['stale_count'])), bordered=True),
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ## Weekly Issue Flow
    """)
    return


@app.cell
def _(load_sql, px, query):
    flow_df = query(load_sql("weekly_flow"))
    fig_flow = px.area(
        flow_df.melt(id_vars='week', value_vars=['opened','closed'], var_name='type', value_name='count'),
        x='week', y='count', color='type',
        color_discrete_map={'opened': '#f38ba8', 'closed': '#a6e3a1'},
        title='Weekly Opened vs Closed'
    )
    fig_flow.update_layout(template='plotly_dark', height=300)
    fig_flow
    return


@app.cell
def _(mo):
    mo.md("""
    ## Resolution Velocity
    """)
    return


@app.cell
def _(load_sql, px, query):
    vel_df = query(load_sql("velocity"))
    fig_vel = px.line(
        vel_df, x='week', y='median_days', color='issue_category',
        color_discrete_map={'bug': '#f38ba8', 'enhancement': '#89b4fa'},
        title='Median Days to Close: Bug vs Enhancement',
        markers=True
    )
    fig_vel.update_layout(template='plotly_dark', height=300)
    fig_vel
    return


@app.cell
def _(mo):
    mo.md("""
    ## Triage Health
    """)
    return


@app.cell
def _(load_sql, mo, query):
    triage = query(load_sql("triage")).iloc[0]
    mo.hstack([
        mo.stat(label="% Labeled", value=f"{int(triage['pct_labeled'])}%", bordered=True),
        mo.stat(label="% Assigned", value=f"{int(triage['pct_assigned'])}%", bordered=True),
        mo.stat(label="% In Milestone", value=f"{int(triage['pct_milestoned'])}%", bordered=True),
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ## Community Priorities (Most-Reacted Open Issues)
    """)
    return


@app.cell
def _(load_sql, px, query):
    top = query(load_sql("community_priorities"))
    top['label'] = top.apply(lambda r: f"#{r['issue_number']} {r['title'][:45]}", axis=1)
    fig_top = px.bar(
        top, x='reactions_total_count', y='label',
        color='issue_category',
        color_discrete_map={'bug': '#f38ba8', 'enhancement': '#89b4fa', 'other': '#a6adc8'},
        orientation='h',
        title='Top Reacted Issues'
    )
    fig_top.update_layout(template='plotly_dark', height=500, yaxis={'categoryorder':'total ascending'})
    fig_top
    return


@app.cell
def _(mo):
    mo.md("""
    ## Assignee Workload
    """)
    return


@app.cell
def _(load_sql, px, query):
    workload = query(load_sql("assignee_workload"))
    fig_wl = px.bar(
        workload.melt(id_vars='assignee_login', value_vars=['bugs','enhancements'], var_name='type', value_name='count'),
        x='count', y='assignee_login', color='type',
        color_discrete_map={'bugs': '#f38ba8', 'enhancements': '#89b4fa'},
        orientation='h',
        title='Open Issues by Assignee', barmode='stack'
    )
    fig_wl.update_layout(template='plotly_dark', height=400, yaxis={'categoryorder':'total ascending'})
    fig_wl
    return


if __name__ == "__main__":
    app.run()
