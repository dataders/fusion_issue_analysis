-- title: Time to First Response (hours)
-- blurb: Weekly p25/p50/p75 of hours from issue creation to first team response.
SELECT
    strftime(date_trunc('week', created_at), '%Y-%m-%d') AS week,
    round(quantile_cont(hours_to_first_response, 0.25), 1) AS p25,
    round(quantile_cont(hours_to_first_response, 0.50), 1) AS p50,
    round(quantile_cont(hours_to_first_response, 0.75), 1) AS p75
FROM fct_issues
WHERE hours_to_first_response IS NOT NULL AND issue_category != 'epic'
GROUP BY date_trunc('week', created_at)
HAVING count(*) >= 3
ORDER BY week
VISUALISE week AS x, p50 AS y
DRAW line
LABEL title => 'Time to First Response (hours) — p50 shown; p25/p75 in data'
