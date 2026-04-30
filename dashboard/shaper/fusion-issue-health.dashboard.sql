-- shaperid:fusion_issue_health_bakeoff

SELECT 'dbt-fusion issue health'::SECTION;

SELECT 'Open source Shaper dashboard source for the bakeoff. Runs on the shared dbt dashboard marts in DuckDB or MotherDuck.'::TEXT_SMALL;

CREATE TEMP VIEW scoped_issues AS (
  SELECT *
  FROM fct_issues
  WHERE issue_category != 'epic'
);

SELECT 'Issue category'::LABEL;

SELECT
  issue_category::DROPDOWN_MULTI AS issue_category,
  count(*)::HINT
FROM scoped_issues
WHERE state = 'OPEN'
GROUP BY issue_category
ORDER BY issue_category;

CREATE TEMP VIEW filtered_issues AS (
  SELECT *
  FROM scoped_issues
  WHERE issue_category IN getvariable('issue_category')
);

SELECT open_issues AS "Open Issues"
FROM summary_kpis;

SELECT (closed_4w - opened_4w) AS "Net Flow (4wk)"
FROM summary_kpis;

SELECT rolling_median_close_days AS "Median Close (days)"
FROM summary_kpis;

SELECT coalesce(pct_responded_48h / 100.0, 0)::GAUGE_PERCENT AS "48h Response SLA"
FROM summary_kpis;

SELECT 'Cumulative issue flow'::LABEL;

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

SELECT 'Open issue age by category'::LABEL;

SELECT
  age_bucket::XAXIS AS "Age",
  issue_count::BARCHART_STACKED AS "Issues",
  issue_category::CATEGORY
FROM age_distribution
WHERE issue_category IN getvariable('issue_category')
ORDER BY
  CASE age_bucket
    WHEN '0-7d' THEN 1
    WHEN '8-30d' THEN 2
    WHEN '31-90d' THEN 3
    WHEN '91-180d' THEN 4
    ELSE 5
  END,
  issue_category;

SELECT 'First response time percentiles'::LABEL;

SELECT
  week::DATE::XAXIS,
  p50::LINECHART AS "Median hours"
FROM response_pctiles
ORDER BY week;

SELECT ('fusion-open-issues-' || today())::DOWNLOAD_CSV AS "CSV";

SELECT *
FROM open_issues_table
WHERE type IN getvariable('issue_category')
ORDER BY age_days DESC;

SELECT 'Oldest open issues'::LABEL;

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

SELECT 'https://github.com/dbt-labs/dbt-fusion/issues'::FOOTER_LINK;
