WITH opened AS (
    SELECT date_trunc('week', created_at)::date as week, count(*) as opened
    FROM fct_issues WHERE issue_category != 'epic' GROUP BY 1
),
closed AS (
    SELECT date_trunc('week', closed_at)::date as week, count(*) as closed
    FROM fct_issues WHERE closed_at IS NOT NULL AND issue_category != 'epic' GROUP BY 1
)
SELECT
    strftime(coalesce(o.week, c.week), '%Y-%m-%d') as week,
    coalesce(o.opened, 0) as opened,
    coalesce(c.closed, 0) as closed
FROM opened o FULL OUTER JOIN closed c ON o.week = c.week
ORDER BY 1
