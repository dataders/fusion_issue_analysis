-- title: Cumulative Issue Flow
-- blurb: Running total of opened vs closed issues over time (excludes EPICs). Gap = issue debt.
SELECT
    week,
    'opened' AS series,
    cumulative_opened AS issues
FROM cumulative_flow
UNION ALL
SELECT
    week,
    'closed' AS series,
    cumulative_closed AS issues
FROM cumulative_flow
ORDER BY week
VISUALISE week AS x, issues AS y, series AS fill
DRAW area
LABEL title => 'Cumulative Issue Flow'
