-- title: Open Issues by Assignee
-- blurb: Active assignees ranked by open workload, split by bug vs enhancement.
SELECT assignee_login, 'bugs' AS type, bugs AS open_issues
FROM assignee_workload
UNION ALL
SELECT assignee_login, 'enhancements' AS type, enhancements AS open_issues
FROM assignee_workload
ORDER BY open_issues DESC
LIMIT 15
VISUALISE assignee_login AS y, open_issues AS x, type AS fill
DRAW bar
LABEL title => 'Open Issues by Assignee'
