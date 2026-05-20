-- shaperid:j66rhu7ey1h1dve95hcnypuk
-- shapersync:2026-05-20T09:31:58Z

select 'Fusion Issue Analysis'::section;

select concat('fusion-issue-report-', today())::download_pdf as PDF;

select open_issues as "Open Issues" from fusion_issues.summary_kpis;
select closed_4w - opened_4w as "Net Flow" from fusion_issues.summary_kpis;
select (pct_responded_48h / 100)::percent as "48h Response SLA" from fusion_issues.summary_kpis;
select stale_count as "Stale Issues" from fusion_issues.summary_kpis;


select 'Cumulative Issue Flow'::section;

select 'Weekly Opened vs Closed (non-cumulative)'::label;
select
  week::xaxis,
  value::barchart_stacked,
  category::category
from (
  select
    week,
    sum(opened) over (order by week) as opened,
    sum(closed) over (order by week) as closed
  from fusion_issues.weekly_flow
)
unpivot (value for category in (opened, closed))
order by week;

select 'Open Issues by Category'::label;
SELECT col1::donutchart, col0::category
FROM (
  VALUES
    ('bug', 165),
    ('enhancement', 113),
    ('other', 53),
);


select 'Velocity & Response'::section;
select 'Median Days to Close: Bugs vs Enhancements'::label;
select
  week::xaxis,
  issue_category::category,
  median_days::linechart
from fusion_issues.velocity order by week;

select 'Time to First Response (hours)'::label;
select
  week::xaxis,
  value::linechart,
  percentile::category
from fusion_issues.response_pctiles
unpivot (value for percentile in (p25, p50, p75))
order by week;


select 'Issue Distribution'::section;
select 'Open Issue Age by Type'::label;
select
  age_bucket::xaxis,
  issue_category::category,
  issue_count::barchart_stacked
from (
  select *, sum(issue_count) over (partition by age_bucket) as total
  from fusion_issues.age_distribution
)
order by total;

select 'Median Days to Close by Label'::label;
select
  label_name::xaxis,
  median_days_to_close::barchart,
  closed_count as "# Closed Issues"
from fusion_issues.close_by_label
order by median_days_to_close desc;


select 'Triage Health'::section;
select (pct_labeled / 100)::percent as "Have labels"
  from fusion_issues.triage_health;
select (pct_typed / 100)::percent as "Have type"
  from fusion_issues.triage_health;
select (pct_assigned / 100)::percent as "Are assigned"
  from fusion_issues.triage_health;
select (pct_milestoned / 100)::percent as "In a milestoned"
  from fusion_issues.triage_health;


select 'Workload & Priorities'::section;
select 'Open Issues by Assignee'::label;
select
  assignee_login::yaxis,
  value::barchart_stacked,
  category::category
from (
  select *, bugs + enhancements as total
  from fusion_issues.assignee_workload
)
unpivot (value for category in (bugs, enhancements))
order by total;

select 'search issues...'::input as search;

select 'filter by category'::label;
select issue_category::dropdown_multi as category_filter from fusion_issues.community_priorities group by all order by all;

select 'Community Priorities'::label;
select
  issue_number,
  title,
  issue_category,
  reactions_total_count,
  age_days
from fusion_issues.community_priorities
where issue_category in getvariable('category_filter')
  and title ilike concat('%', getvariable('search'), '%')
order by reactions_total_count desc;


select ''::section;
select 'Shaper implementation of the dashboard from:
https://github.com/dataders/fusion_issues

More about Shaper:
https://taleshape.com/shaper/docs';