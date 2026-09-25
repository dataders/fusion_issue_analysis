-- shaperid:fusion_issue_health_bakeoff
--
-- Renders the tile contract in dashboard/tiles.yml. Every query is a thin
-- read of one dbt dashboard model (transform/models/dashboard/), ordered by
-- the tile's order_by. Shaper-specific work is limited to type casts, labels,
-- palette colors (tiles.yml palette, via ::COLOR) and light unpivots.

SELECT 'dbt Fusion issue health'::SECTION,
  'Open engine:v2 issues in dbt-labs/dbt-core (epics excluded unless noted)'::SUBTITLE;

-- Freshness banner (dashboard_meta). The warning row only exists when
-- days_stale > stale_after_days (3).
SELECT ('Data as of ' || strftime(as_of_date, '%Y-%m-%d')
    || ' · ' || source_repo || ' · label ' || source_label)::TEXT_SMALL
FROM dashboard_meta;

SELECT ('⚠ Data is ' || days_stale || ' days old — the extract has probably stopped.')::TEXT_MEDIUM
FROM dashboard_meta
WHERE days_stale > 3;

-- ────────────────────────────────────────────────────────────────
-- Where do things stand?  (headline_kpis)
-- ────────────────────────────────────────────────────────────────

SELECT 'Where do things stand?'::SECTION;

SELECT open_issues AS "Open issues",
  printf('%+d in 28 days', backlog_change_28d)::SUBTITLE
FROM headline_kpis;

SELECT opened_28d || ' / ' || closed_28d AS "Opened / closed (28d)"
FROM headline_kpis;

SELECT awaiting_triage AS "Awaiting triage",
  ('median age ' || awaiting_triage_median_age_days::INTEGER || ' days')::SUBTITLE
FROM headline_kpis;

SELECT pct_responded_48h_28d::INTEGER || '%' AS "Answered within 48h (28d)",
  printf('median first reply %g h', median_hours_to_first_response_28d)::SUBTITLE
FROM headline_kpis;

SELECT median_days_to_close_28d AS "Median days to close (28d)"
FROM headline_kpis;

SELECT open_customer_reported AS "Customer-reported open",
  (open_hard_blockers || ' hard blockers')::SUBTITLE
FROM headline_kpis;

-- ────────────────────────────────────────────────────────────────
-- Is the backlog shrinking?
-- ────────────────────────────────────────────────────────────────

SELECT 'Is the backlog shrinking?'::SECTION;

-- Shaper has no stacked area; stacked bars per week are the closest idiom.
SELECT 'Open issues over time'::LABEL,
  'Open at the end of each week, by type'::SUBTITLE;

SELECT
  week::DATE::XAXIS,
  open_issues::BARCHART_STACKED AS "Open issues",
  issue_category::CATEGORY,
  CASE issue_category
    WHEN 'feature' THEN '#2a78d6'
    WHEN 'bug' THEN '#eb6834'
    WHEN 'task' THEN '#1baf7a'
    ELSE '#898781'
  END::COLOR
FROM backlog_weekly
ORDER BY week, CASE issue_category WHEN 'feature' THEN 1 WHEN 'bug' THEN 2 WHEN 'task' THEN 3 ELSE 4 END;

SELECT 'Opened vs closed per week'::LABEL,
  'Complete weeks; when closed > opened the backlog shrank'::SUBTITLE;

-- Unpivot the opened / closed series (palette.flow). Grouped, not stacked.
SELECT week::DATE::XAXIS, opened::BARCHART AS "Issues", 'opened'::CATEGORY, '#eb6834'::COLOR
FROM weekly_flow
UNION ALL
SELECT week::DATE::XAXIS, closed::BARCHART AS "Issues", 'closed'::CATEGORY, '#2a78d6'::COLOR
FROM weekly_flow
ORDER BY 1, 3 DESC;

-- ────────────────────────────────────────────────────────────────
-- Are we keeping up with triage?
-- ────────────────────────────────────────────────────────────────

SELECT 'Are we keeping up with triage?'::SECTION;

SELECT 'Open issues by triage status and age'::LABEL,
  'How much is waiting, and for how long'::SUBTITLE;

SELECT
  status_label::YAXIS AS "Triage status",
  issue_count::BARCHART_STACKED AS "Open issues",
  age_bucket::CATEGORY,
  CASE age_bucket
    WHEN '0-7d' THEN '#b7d3f6'
    WHEN '8-30d' THEN '#86b6ef'
    WHEN '31-90d' THEN '#5598e7'
    WHEN '91-180d' THEN '#256abf'
    ELSE '#104281'
  END::COLOR
FROM triage_pipeline
ORDER BY status_order, age_bucket_order;

SELECT 'New issues answered within 48 hours'::LABEL,
  'By week opened; unanswered issues count as misses'::SUBTITLE;

SELECT
  week::DATE::XAXIS,
  (pct_responded_48h / 100.0)::LINECHART_PERCENT AS "Answered within 48h",
  '#2a78d6'::COLOR
FROM response_weekly
ORDER BY week;

SELECT 'Triage queue — oldest first'::LABEL,
  'Open issues still labeled status:triage'::SUBTITLE;

SELECT
  issue_number AS "#",
  title,
  issue_category AS "type",
  age_days,
  days_idle,
  reactions,
  comments,
  is_customer_reported AS "customer",
  issue_url::HYPERLINK AS "Link"
FROM triage_queue
ORDER BY age_days DESC;

-- ────────────────────────────────────────────────────────────────
-- Where is the work?
-- ────────────────────────────────────────────────────────────────

SELECT 'Where is the work?'::SECTION;

SELECT 'Open issues by area'::LABEL,
  'Issues with several areas count in each'::SUBTITLE;

SELECT
  area::YAXIS AS "Area",
  issue_count::BARCHART_STACKED AS "Open issues",
  issue_category::CATEGORY,
  CASE issue_category
    WHEN 'feature' THEN '#2a78d6'
    WHEN 'bug' THEN '#eb6834'
    WHEN 'task' THEN '#1baf7a'
    ELSE '#898781'
  END::COLOR
FROM open_by_area
ORDER BY area_total DESC, area, CASE issue_category WHEN 'feature' THEN 1 WHEN 'bug' THEN 2 WHEN 'task' THEN 3 ELSE 4 END;

SELECT 'Open issues by adapter'::LABEL,
  '(none) = adapter-agnostic'::SUBTITLE;

SELECT
  adapter::YAXIS AS "Adapter",
  issue_count::BARCHART_STACKED AS "Open issues",
  issue_category::CATEGORY,
  CASE issue_category
    WHEN 'feature' THEN '#2a78d6'
    WHEN 'bug' THEN '#eb6834'
    WHEN 'task' THEN '#1baf7a'
    ELSE '#898781'
  END::COLOR
FROM open_by_adapter
ORDER BY adapter_total DESC, adapter, CASE issue_category WHEN 'feature' THEN 1 WHEN 'bug' THEN 2 WHEN 'task' THEN 3 ELSE 4 END;

-- ────────────────────────────────────────────────────────────────
-- How close are the epics?
-- ────────────────────────────────────────────────────────────────

SELECT 'How close are the epics?'::SECTION;

SELECT 'Open epics by % of sub-issues closed'::LABEL,
  'Top of the list can be closed out soon'::SUBTITLE;

SELECT
  epic_number AS "#",
  title,
  child_closed AS "closed",
  child_total AS "sub-issues",
  (pct_complete / 100.0)::PERCENT AS "% complete",
  milestone_title AS "milestone",
  issue_url::HYPERLINK AS "Link"
FROM epic_progress
ORDER BY pct_complete DESC, child_open, epic_number;

-- ────────────────────────────────────────────────────────────────
-- What should we work on, and who is on it?
-- ────────────────────────────────────────────────────────────────

SELECT 'What should we work on, and who is on it?'::SECTION;

SELECT 'Most-requested open issues'::LABEL,
  'Ranked by reactions, then comments'::SUBTITLE;

SELECT
  issue_number AS "#",
  title,
  issue_category AS "type",
  areas,
  triage_status AS "triage",
  reactions,
  comments,
  age_days,
  is_customer_reported AS "customer",
  issue_url::HYPERLINK AS "Link"
FROM top_requested
ORDER BY reactions DESC, comments DESC;

SELECT 'Open issues by assignee'::LABEL,
  'Top 15, including unassigned'::SUBTITLE;

SELECT
  assignee_login::YAXIS AS "Assignee",
  issue_count::BARCHART_STACKED AS "Open issues",
  issue_category::CATEGORY,
  CASE issue_category
    WHEN 'feature' THEN '#2a78d6'
    WHEN 'bug' THEN '#eb6834'
    WHEN 'task' THEN '#1baf7a'
    ELSE '#898781'
  END::COLOR
FROM assignee_workload
ORDER BY assignee_total DESC, assignee_login, CASE issue_category WHEN 'feature' THEN 1 WHEN 'bug' THEN 2 WHEN 'task' THEN 3 ELSE 4 END;

SELECT 'https://github.com/dbt-labs/dbt-core/issues?q=label%3Aengine%3Av2'::FOOTER_LINK;
