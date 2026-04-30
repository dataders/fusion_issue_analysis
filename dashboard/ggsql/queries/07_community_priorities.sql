-- title: Community Priorities
-- blurb: Most-reacted open issues — a proxy for user-facing importance.
SELECT
    issue_number,
    title,
    issue_category,
    reactions_total_count
FROM community_priorities
ORDER BY reactions_total_count DESC
LIMIT 15
VISUALISE title AS y, reactions_total_count AS x, issue_category AS fill
DRAW bar
LABEL title => 'Community Priorities'
