-- title: Issues opened per week
-- blurb: Weekly count of newly-opened Fusion issues.
SELECT
    DATE_TRUNC('week', created_at) AS week,
    COUNT(*) AS issues_opened
FROM fct_issues
GROUP BY week
ORDER BY week
VISUALISE week AS x, issues_opened AS y
DRAW line
LABEL title => 'Issues opened per week'
