-- title: Top authors by issues opened
-- blurb: Heaviest issue-reporters across the project.
SELECT * FROM top_authors
VISUALISE author_login AS y, issues_opened AS x
DRAW bar
LABEL title => 'Top 15 issue authors'
