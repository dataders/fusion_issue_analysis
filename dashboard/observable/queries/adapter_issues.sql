SELECT
    issue_number,
    title,
    type,
    days_open,
    reactions,
    milestone
FROM adapter_issues
ORDER BY reactions DESC, days_open DESC
