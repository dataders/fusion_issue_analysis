-- title: Community Priorities
-- blurb: Most-reacted open issues — a proxy for user-facing importance.
-- type: table
SELECT
    issue_number,
    issue_url,
    title,
    issue_category,
    reactions_total_count
FROM community_priorities
ORDER BY reactions_total_count DESC
LIMIT 15
