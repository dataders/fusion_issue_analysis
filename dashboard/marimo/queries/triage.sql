SELECT
    round(sum(is_labeled::int)*100.0/count(*), 0) AS pct_labeled,
    round(sum(is_assigned::int)*100.0/count(*), 0) AS pct_assigned,
    round(sum(has_milestone::int)*100.0/count(*), 0) AS pct_milestoned
FROM fct_issues WHERE state='OPEN' AND issue_category!='epic'
