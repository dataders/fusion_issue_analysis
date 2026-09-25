-- tile: assignee_workload
-- order: y
SELECT
    assignee_login,
    CASE issue_category WHEN 'feature' THEN '1 feature' WHEN 'bug' THEN '2 bug'
        WHEN 'task' THEN '3 task' ELSE '4 other' END AS issue_type,
    issue_count
FROM assignee_workload
ORDER BY assignee_total DESC, assignee_login
VISUALISE issue_count AS x, assignee_login AS y, issue_type AS fill
DRAW bar
SCALE DISCRETE fill FROM ['1 feature', '2 bug', '3 task', '4 other']
    TO ['#2a78d6', '#eb6834', '#1baf7a', '#898781']
    RENAMING '1 feature' => 'Feature', '2 bug' => 'Bug', '3 task' => 'Task', '4 other' => 'Other'
LABEL x => 'Open issues', y => null, fill => 'Type'
