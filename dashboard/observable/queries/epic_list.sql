SELECT
    issue_number,
    title,
    days_open,
    milestone_title,
    reactions_total_count
FROM epic_list
WHERE state = 'OPEN'
ORDER BY days_open DESC
