-- tile: triage_queue
-- type: table
SELECT issue_number, title, issue_category, age_days, days_idle, reactions, comments,
       is_customer_reported, issue_url
FROM triage_queue
ORDER BY age_days DESC
