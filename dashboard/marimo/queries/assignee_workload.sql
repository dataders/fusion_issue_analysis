SELECT a.assignee_login,
       count(*) AS open_issues,
       count(CASE WHEN f.issue_category='bug' THEN 1 END) AS bugs,
       count(CASE WHEN f.issue_category='enhancement' THEN 1 END) AS enhancements
FROM stg_issue_assignees a
INNER JOIN fct_issues f ON a.issue_dlt_id = f.issue_dlt_id
WHERE f.state='OPEN' AND f.issue_category!='epic'
GROUP BY a.assignee_login
ORDER BY open_issues DESC LIMIT 15
