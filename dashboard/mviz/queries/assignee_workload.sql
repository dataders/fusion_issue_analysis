select
    a.assignee_login,
    count(*) as open_issues,
    count(case when f.issue_category = 'bug' then 1 end) as bugs,
    count(case when f.issue_category = 'enhancement' then 1 end) as enhancements
from stg_issue_assignees a
inner join fct_issues f on a.issue_dlt_id = f.issue_dlt_id
where f.state = 'OPEN' and f.issue_category != 'epic'
group by a.assignee_login
order by open_issues desc
limit 15
