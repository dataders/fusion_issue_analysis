-- title: Open vs closed by category
-- blurb: Composition of current backlog by derived issue_category.
SELECT
    issue_category,
    state,
    COUNT(*) AS n
FROM fct_issues
GROUP BY issue_category, state
VISUALISE issue_category AS x, n AS y, state AS fill
DRAW bar
LABEL title => 'Issues by category and state'
