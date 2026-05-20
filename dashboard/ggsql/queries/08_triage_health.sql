-- title: Triage Health
-- blurb: Single-row operational counts across the open-issue triage taxonomy.
-- type: kpi
SELECT
    slipped_through_count,
    triage_queue_count,
    hard_blocker_count,
    stale_count,
    needs_repro_count,
    repro_verified_count
FROM issue_triage_health
