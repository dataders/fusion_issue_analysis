SELECT
    l.label_name,
    round(median(f.hours_to_close) / 24, 1) as median_days_to_close,
    count(*) as closed_count
FROM fct_issues f
INNER JOIN fct_issue_labels l ON f.issue_dlt_id = l.issue_dlt_id
WHERE f.closed_at IS NOT NULL AND f.issue_category != 'epic'
GROUP BY l.label_name
HAVING count(*) >= 10
ORDER BY median_days_to_close DESC
LIMIT 15
