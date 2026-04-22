-- title: Median Days to Close: Bugs vs Enhancements
-- blurb: Weekly median close time by issue type. Tracks resolution velocity trends.
SELECT
    strftime(date_trunc('week', closed_at), '%Y-%m-%d') AS week,
    issue_category,
    round(median(hours_to_close) / 24, 1) AS median_days
FROM fct_issues
WHERE closed_at IS NOT NULL AND issue_category IN ('bug', 'enhancement')
GROUP BY 1, 2
HAVING count(*) >= 2
ORDER BY 1
VISUALISE week AS x, median_days AS y, issue_category AS color
DRAW line
LABEL title => 'Median Days to Close: Bugs vs Enhancements'
