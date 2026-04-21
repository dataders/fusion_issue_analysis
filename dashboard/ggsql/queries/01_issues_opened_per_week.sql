-- title: Issues opened per week
-- blurb: Weekly count of newly-opened Fusion issues.
SELECT * FROM issues_opened_per_week
VISUALISE week AS x, issues_opened AS y
DRAW line
LABEL title => 'Issues opened per week'
