-- tile: open_by_area
-- order: y
SELECT
    area,
    CASE issue_category WHEN 'feature' THEN '1 feature' WHEN 'bug' THEN '2 bug'
        WHEN 'task' THEN '3 task' ELSE '4 other' END AS issue_type,
    issue_count
FROM open_by_area
ORDER BY area_total DESC, area
VISUALISE issue_count AS x, area AS y, issue_type AS fill
DRAW bar
SCALE DISCRETE fill FROM ['1 feature', '2 bug', '3 task', '4 other']
    TO ['#2a78d6', '#eb6834', '#1baf7a', '#898781']
    RENAMING '1 feature' => 'Feature', '2 bug' => 'Bug', '3 task' => 'Task', '4 other' => 'Other'
LABEL x => 'Open issues', y => null, fill => 'Type'
