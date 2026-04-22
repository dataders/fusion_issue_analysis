-- title: Cumulative Issue Flow
-- blurb: Running total of opened vs closed issues over time (excludes EPICs). Gap = issue debt.
WITH weeks AS (
    SELECT
        date_trunc('week', created_at)::date AS week,
        count(*) AS opened
    FROM fct_issues WHERE issue_category != 'epic'
    GROUP BY 1
),
closed_weeks AS (
    SELECT
        date_trunc('week', closed_at)::date AS week,
        count(*) AS closed
    FROM fct_issues WHERE closed_at IS NOT NULL AND issue_category != 'epic'
    GROUP BY 1
),
combined AS (
    SELECT
        coalesce(w.week, c.week) AS week,
        coalesce(w.opened, 0) AS opened,
        coalesce(c.closed, 0) AS closed
    FROM weeks w
    FULL OUTER JOIN closed_weeks c ON w.week = c.week
)
SELECT
    strftime(week, '%Y-%m-%d') AS week,
    sum(opened) OVER (ORDER BY week) AS cumulative_opened,
    sum(closed) OVER (ORDER BY week) AS cumulative_closed
FROM combined
ORDER BY week
VISUALISE week AS x, cumulative_opened AS y
DRAW area
LABEL title => 'Cumulative Issue Flow'
