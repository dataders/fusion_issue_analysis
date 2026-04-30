-- title: Cumulative Issue Flow
-- blurb: Running total of opened vs closed issues over time (excludes EPICs). Gap = issue debt.
SELECT
    week,
    'opened' AS series,
    cumulative_opened::DOUBLE AS issues
FROM cumulative_flow
UNION ALL
SELECT
    week,
    'closed' AS series,
    cumulative_closed::DOUBLE AS issues
FROM cumulative_flow
ORDER BY series, week
VISUALISE week AS x, issues AS y, series AS fill
DRAW area
PARTITION BY series
SCALE x VIA date
LABEL title => 'Cumulative Issue Flow'
