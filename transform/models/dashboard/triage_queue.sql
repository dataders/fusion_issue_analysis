{#
  Q: Which issues should be triaged next?
  Open issues still carrying the triage label, oldest first.
#}

with a as (select as_of_date from {{ ref('as_of') }})

select
    f.issue_number,
    f.title,
    f.issue_category,
    date_diff('day', f.created_at, a.as_of_date) as age_days,
    date_diff('day', f.updated_at, a.as_of_date) as days_idle,
    f.reactions_total_count as reactions,
    f.comments_total_count as comments,
    f.is_customer_reported,
    f.issue_url
from {{ ref('fct_issues') }} f cross join a
where f.state = 'OPEN'
  and f.issue_category != 'epic'
  and f.triage_status = 'awaiting_triage'
order by f.created_at
limit 50
