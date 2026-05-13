SELECT
    assignee_login,
    open_issues
FROM fusion_issues.main.assignee_workload
WHERE assignee_login IS NOT NULL
ORDER BY open_issues DESC
LIMIT 12
