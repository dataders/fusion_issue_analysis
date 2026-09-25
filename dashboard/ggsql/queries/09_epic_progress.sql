-- tile: epic_progress
-- type: table
SELECT epic_number, title, child_closed, child_total, pct_complete, milestone_title, issue_url
FROM epic_progress
ORDER BY pct_complete DESC, child_open, epic_number
