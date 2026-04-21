SELECT issue_number, title, issue_category, reactions_total_count,
       round(datediff('day', created_at, current_date), 0) AS age_days
FROM fct_issues
WHERE state='OPEN' AND reactions_total_count > 0 AND issue_category!='epic'
ORDER BY reactions_total_count DESC LIMIT 15
