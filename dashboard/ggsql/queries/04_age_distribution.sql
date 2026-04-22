-- title: Open Issue Age by Type
-- blurb: Count of open issues bucketed by age, split by bug/enhancement/other.
SELECT
    issue_category,
    CASE
        WHEN datediff('day', created_at, current_date) <= 7 THEN '0-7d'
        WHEN datediff('day', created_at, current_date) <= 30 THEN '8-30d'
        WHEN datediff('day', created_at, current_date) <= 90 THEN '31-90d'
        WHEN datediff('day', created_at, current_date) <= 180 THEN '91-180d'
        ELSE '180d+'
    END AS age_bucket,
    count(*) AS issue_count
FROM fct_issues
WHERE state = 'OPEN' AND issue_category != 'epic'
GROUP BY 1, 2
ORDER BY issue_category, min(datediff('day', created_at, current_date))
VISUALISE age_bucket AS x, issue_count AS y, issue_category AS fill
DRAW bar
LABEL title => 'Open Issue Age by Type'
