-- title: Top authors by issues opened
-- blurb: Heaviest issue-reporters across the project.
SELECT
    author_login,
    COUNT(*) AS issues_opened
FROM fct_issues
WHERE author_login IS NOT NULL
GROUP BY author_login
ORDER BY issues_opened DESC
LIMIT 15
VISUALISE author_login AS y, issues_opened AS x
DRAW bar
LABEL title => 'Top 15 issue authors'
