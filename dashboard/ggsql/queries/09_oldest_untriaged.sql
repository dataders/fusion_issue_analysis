-- title: Oldest Untriaged Issues
-- blurb: Top-25 open non-EPIC issues with zero triage signal — the daily action queue.
-- type: table
SELECT
    issue_number,
    title,
    author_login,
    issue_category,
    reactions_total_count,
    comments_total_count,
    age_days,
    days_since_activity,
    issue_url
FROM oldest_untriaged
ORDER BY age_days DESC
