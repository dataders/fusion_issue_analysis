-- tile: backlog_weekly
-- Category names are prefixed with their palette order so ggsql stacks them
-- feature, bug, task, other; RENAMING restores the labels.
SELECT
    week::DATE AS week,
    CASE issue_category WHEN 'feature' THEN '1 feature' WHEN 'bug' THEN '2 bug'
        WHEN 'task' THEN '3 task' ELSE '4 other' END AS issue_type,
    open_issues
FROM backlog_weekly
ORDER BY week
VISUALISE week AS x, open_issues AS y, issue_type AS fill
DRAW area
SCALE x VIA date
SCALE DISCRETE fill FROM ['1 feature', '2 bug', '3 task', '4 other']
    TO ['#2a78d6', '#eb6834', '#1baf7a', '#898781']
    RENAMING '1 feature' => 'Feature', '2 bug' => 'Bug', '3 task' => 'Task', '4 other' => 'Other'
LABEL x => null, y => 'Open issues', fill => 'Type'
