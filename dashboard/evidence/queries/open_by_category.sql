SELECT
    issue_category,
    count(*) as count
FROM fct_issues
WHERE state = 'OPEN' AND issue_category != 'epic'
GROUP BY issue_category
ORDER BY count DESC
