-- title: Open Issues by Assignee
-- blurb: Active assignees ranked by open workload, split by bug vs enhancement.
SELECT
    a.assignee_login,
    count(*) AS open_issues
FROM stg_issue_assignees a
INNER JOIN fct_issues f ON a.issue_dlt_id = f.issue_dlt_id
WHERE f.state = 'OPEN' AND f.issue_category != 'epic'
GROUP BY a.assignee_login
ORDER BY open_issues DESC
LIMIT 15
VISUALISE assignee_login AS y, open_issues AS x
DRAW bar
LABEL title => 'Open Issues by Assignee'
