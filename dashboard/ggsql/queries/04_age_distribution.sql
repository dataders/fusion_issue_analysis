-- title: Open Issue Age by Type
-- blurb: Count of open issues bucketed by age, split by bug/enhancement/other.
SELECT age_bucket, issue_category, issue_count
FROM age_distribution
VISUALISE age_bucket AS x, issue_count AS y, issue_category AS fill
DRAW bar
LABEL title => 'Open Issue Age by Type'
