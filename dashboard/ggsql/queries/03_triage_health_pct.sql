-- title: Triage Health
-- blurb: Percentage of open issues that have been labeled, typed, assigned, and milestoned.
-- type: kpi
SELECT
    pct_labeled,
    pct_typed,
    pct_assigned,
    pct_milestoned
FROM triage_health
