-- title: Open vs closed by category
-- blurb: Composition of current backlog by derived issue_category.
SELECT * FROM open_vs_closed_by_category
VISUALISE issue_category AS x, n AS y, state AS fill
DRAW bar
LABEL title => 'Issues by category and state'
