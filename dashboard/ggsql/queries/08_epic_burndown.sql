-- title: EPIC Burndown
-- blurb: Open EPICs ranked by age — the longer a bar, the longer it's been blocking work.
SELECT
    issue_number,
    title,
    days_open,
    coalesce(milestone_title, 'No Milestone') AS milestone
FROM epic_list
WHERE state = 'OPEN'
ORDER BY days_open DESC
VISUALISE days_open AS x, title AS y, milestone AS fill
DRAW bar
LABEL title => 'EPIC Burndown'
