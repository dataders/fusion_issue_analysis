-- title: Key Metrics
-- blurb: High-level health snapshot: backlog size, net flow, close speed, response SLA, staleness.
-- type: kpi
SELECT
    open_issues,
    printf('%+d', net_flow_4w) AS net_flow_4w,
    rolling_median_close_days,
    pct_responded_48h,
    stale_count
FROM summary_kpis
