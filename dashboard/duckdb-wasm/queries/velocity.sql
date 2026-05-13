SELECT
    week,
    max(CASE WHEN issue_category = 'bug' THEN median_days END)         AS bugs,
    max(CASE WHEN issue_category = 'enhancement' THEN median_days END) AS enhancements
FROM fusion_issues.main.velocity
GROUP BY week
ORDER BY week
