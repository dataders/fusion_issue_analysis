SELECT
    round(sum(is_labeled::int)*100.0/count(*), 0) as pct_labeled,
    round(sum(is_assigned::int)*100.0/count(*), 0) as pct_assigned,
    round(sum(has_milestone::int)*100.0/count(*), 0) as pct_milestoned,
    round(count(case when issue_category != 'other' then 1 end)*100.0/count(*), 0) as pct_typed,
    count(*) as total_open
FROM fct_issues
WHERE state = 'OPEN' AND issue_category != 'epic'
