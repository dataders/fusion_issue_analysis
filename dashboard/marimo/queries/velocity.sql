SELECT strftime(date_trunc('week', closed_at), '%Y-%m-%d') AS week,
       issue_category,
       round(median(hours_to_close)/24.0, 1) AS median_days,
       count(*) AS n
FROM fct_issues
WHERE closed_at IS NOT NULL AND issue_category IN ('bug','enhancement')
GROUP BY 1, 2
HAVING count(*) >= 2
ORDER BY 1
