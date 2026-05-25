-- Open issues tagged with the 'adapter' label, ordered by community interest then age
select
    i.issue_number,
    i.title,
    i.issue_category as type,
    coalesce(i.milestone_title, '') as milestone,
    i.reactions_total_count as reactions,
    i.comments_total_count as comments,
    round(datediff('day', i.created_at, current_date), 0) as days_open
from {{ ref('fct_issues') }} i
inner join {{ ref('fct_issue_labels') }} il
    on i.issue_dlt_id = il.issue_dlt_id
where il.label_name = 'adapter'
  and i.state = 'OPEN'
order by i.reactions_total_count desc, days_open desc
