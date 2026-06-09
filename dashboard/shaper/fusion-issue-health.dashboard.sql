-- shaperid:fusion_issue_health_bakeoff

SELECT 'dbt-fusion Issue Health'::SECTION;

SELECT 'Open source Shaper dashboard — CORE-22 canonical tile set over shared dbt dashboard marts in DuckDB or MotherDuck.'::TEXT_SMALL;

SELECT 'Issue category'::LABEL;

SELECT
  issue_category::DROPDOWN_MULTI AS issue_category,
  count::HINT
FROM open_by_category
ORDER BY issue_category;

-- ────────────────────────────────────────────────────────────────
-- [Operational Triage]
-- ────────────────────────────────────────────────────────────────

SELECT 'Operational Triage'::SECTION;

SELECT slipped_through_count AS "Slipped Through (bugs)"
FROM issue_triage_health;

SELECT triage_queue_count AS "Triage Queue"
FROM issue_triage_health;

SELECT hard_blocker_count AS "Hard Blockers"
FROM issue_triage_health;

SELECT stale_count AS "Stale (90d+)"
FROM issue_triage_health;

SELECT needs_repro_count AS "Needs Repro"
FROM issue_triage_health;

SELECT repro_verified_count AS "Repro Verified"
FROM issue_triage_health;

SELECT total_open AS "Total Open"
FROM issue_triage_health;

SELECT 'Oldest Untriaged Bugs'::LABEL;

SELECT
  issue_number AS "#",
  title,
  age_days,
  issue_url::HYPERLINK AS "Link"
FROM oldest_untriaged
ORDER BY age_days DESC
LIMIT 20;

-- ────────────────────────────────────────────────────────────────
-- [Key Metrics]
-- ────────────────────────────────────────────────────────────────

SELECT 'Key Metrics'::SECTION;

SELECT open_issues AS "Open Issues"
FROM summary_kpis;

SELECT net_flow_4w AS "Net Flow (4 wk)"
FROM summary_kpis;

SELECT rolling_median_close_days AS "Median Close (4 wk)"
FROM summary_kpis;

SELECT coalesce(pct_responded_48h / 100.0, 0)::GAUGE_PERCENT AS "48h Response SLA"
FROM summary_kpis;

SELECT stale_count AS "Stale Issues (30d+)"
FROM summary_kpis;

-- ────────────────────────────────────────────────────────────────
-- [Trends]
-- ────────────────────────────────────────────────────────────────

SELECT 'Trends'::SECTION;

SELECT 'Cumulative Issue Flow'::LABEL;

SELECT
  week::DATE::XAXIS,
  cumulative_opened::LINECHART AS "Issues",
  'opened'::CATEGORY
FROM cumulative_flow
UNION ALL
SELECT
  week::DATE::XAXIS,
  cumulative_closed::LINECHART AS "Issues",
  'closed'::CATEGORY
FROM cumulative_flow
ORDER BY 1, 3;

SELECT 'Median Days to Close: Bugs vs Enhancements'::LABEL;

SELECT
  week::DATE::XAXIS,
  median_days::LINECHART AS "Median Days",
  issue_category::CATEGORY
FROM velocity
WHERE issue_category IN ('bug', 'enhancement')
ORDER BY week, issue_category;

SELECT 'Time to First Response (hours)'::LABEL;

SELECT
  week::DATE::XAXIS,
  p25::LINECHART AS "p25",
  'p25'::CATEGORY
FROM response_pctiles
UNION ALL
SELECT
  week::DATE::XAXIS,
  p50::LINECHART AS "p50",
  'p50'::CATEGORY
FROM response_pctiles
UNION ALL
SELECT
  week::DATE::XAXIS,
  p75::LINECHART AS "p75",
  'p75'::CATEGORY
FROM response_pctiles
ORDER BY 1, 3;

SELECT 'Open Issue Age by Type'::LABEL;

SELECT
  age_bucket::XAXIS AS "Age",
  issue_count::BARCHART_STACKED AS "Issues",
  issue_category::CATEGORY
FROM age_distribution
WHERE issue_category IN getvariable('issue_category')
ORDER BY bucket_sort_order, issue_category;

SELECT 'Median Days to Close by Label'::LABEL;

SELECT
  label_name::XAXIS AS "Label",
  median_days_to_close::BARCHART AS "Median Days"
FROM close_by_label
ORDER BY median_days_to_close DESC
LIMIT 20;

-- ────────────────────────────────────────────────────────────────
-- [Triage Health]
-- ────────────────────────────────────────────────────────────────

SELECT 'Triage Health'::SECTION;

SELECT coalesce(pct_labeled / 100.0, 0)::GAUGE_PERCENT AS "% Labeled"
FROM triage_health;

SELECT coalesce(pct_typed / 100.0, 0)::GAUGE_PERCENT AS "% Typed"
FROM triage_health;

SELECT coalesce(pct_assigned / 100.0, 0)::GAUGE_PERCENT AS "% Assigned"
FROM triage_health;

SELECT coalesce(pct_milestoned / 100.0, 0)::GAUGE_PERCENT AS "% Milestoned"
FROM triage_health;

-- ────────────────────────────────────────────────────────────────
-- [People]
-- ────────────────────────────────────────────────────────────────

SELECT 'People'::SECTION;

SELECT 'Open Issues by Assignee'::LABEL;

SELECT
  assignee_login::XAXIS AS "Assignee",
  bugs::BARCHART_STACKED AS "Issues",
  'bug'::CATEGORY
FROM assignee_workload
UNION ALL
SELECT
  assignee_login::XAXIS AS "Assignee",
  enhancements::BARCHART_STACKED AS "Issues",
  'enhancement'::CATEGORY
FROM assignee_workload
ORDER BY 1, 3;

SELECT 'Community Priorities'::LABEL;

SELECT
  issue_number AS "#",
  title,
  issue_category AS "type",
  reactions_total_count AS "reactions",
  comments_total_count AS "comments",
  age_days,
  issue_url::HYPERLINK AS "Link"
FROM community_priorities
ORDER BY reactions_total_count DESC;

-- ────────────────────────────────────────────────────────────────
-- Open issues table + CSV download
-- ────────────────────────────────────────────────────────────────

SELECT 'Open Issues'::SECTION;

SELECT ('fusion-open-issues-' || today())::DOWNLOAD_CSV AS "CSV";

SELECT
  "#",
  title,
  type,
  age_days,
  reactions,
  comments,
  milestone,
  issue_url::HYPERLINK AS "Link"
FROM open_issues_table
WHERE type IN getvariable('issue_category')
ORDER BY age_days DESC;

SELECT 'Oldest Open Issues'::LABEL;

SELECT
  "#",
  title,
  type,
  age_days,
  reactions,
  comments,
  milestone
FROM open_issues_table
WHERE type IN getvariable('issue_category')
ORDER BY age_days DESC
LIMIT 20;

SELECT 'https://github.com/dbt-labs/dbt-core/issues?q=label%3Av2'::FOOTER_LINK;
