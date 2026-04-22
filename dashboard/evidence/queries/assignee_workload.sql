SELECT
    a.assignee_login,
    count(case when f.issue_category = 'bug' then 1 end) as bugs,
    count(case when f.issue_category = 'enhancement' then 1 end) as enhancements,
    count(*) as open_issues
FROM stg_issue_assignees a
INNER JOIN fct_issues f ON a.issue_dlt_id = f.issue_dlt_id
WHERE f.state = 'OPEN' AND f.issue_category != 'epic'
GROUP BY a.assignee_login
ORDER BY open_issues DESC
LIMIT 15
