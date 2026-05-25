-- title: Adapter Issues
-- blurb: Open issues tagged 'adapter', ranked by community interest (reactions).
SELECT
    issue_number,
    title,
    type,
    days_open,
    reactions
FROM adapter_issues
ORDER BY reactions DESC, days_open DESC
VISUALISE reactions AS x, title AS y, type AS fill
DRAW bar
LABEL title => 'Open Adapter Issues'
