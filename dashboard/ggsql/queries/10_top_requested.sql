-- tile: top_requested
-- type: table
SELECT issue_number, title, issue_category, areas, triage_status, reactions, comments,
       age_days, is_customer_reported, issue_url
FROM top_requested
ORDER BY reactions DESC, comments DESC
