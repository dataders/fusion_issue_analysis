WITH opened AS (
    SELECT date_trunc('week', created_at)::date AS week, count(*) AS opened
    FROM fct_issues WHERE issue_category != 'epic' GROUP BY 1
),
closed AS (
    SELECT date_trunc('week', closed_at)::date AS week, count(*) AS closed
    FROM fct_issues WHERE closed_at IS NOT NULL AND issue_category != 'epic' GROUP BY 1
)
SELECT coalesce(o.week, c.week) AS week,
       coalesce(o.opened, 0) AS opened,
       coalesce(c.closed, 0) AS closed
FROM opened o FULL OUTER JOIN closed c ON o.week = c.week
ORDER BY 1
