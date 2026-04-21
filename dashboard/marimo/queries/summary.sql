SELECT
    count(CASE WHEN state='OPEN' AND issue_category!='epic' THEN 1 END) AS open_issues,
    count(CASE WHEN closed_at >= current_date - INTERVAL '28 days' AND issue_category!='epic' THEN 1 END) AS closed_4w,
    count(CASE WHEN created_at >= current_date - INTERVAL '28 days' AND issue_category!='epic' THEN 1 END) AS opened_4w,
    count(CASE WHEN state='OPEN' AND updated_at < current_date - INTERVAL '30 days' AND issue_category!='epic' THEN 1 END) AS stale_count,
    round(median(CASE WHEN closed_at >= current_date - INTERVAL '28 days' THEN hours_to_close END) / 24.0, 1) AS median_close_days
FROM fct_issues
