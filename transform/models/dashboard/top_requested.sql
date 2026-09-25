{#
  Q: What do users want most?
  Open non-epic issues ranked by reactions, then comments.
#}

with a as (select as_of_date from {{ ref('as_of') }}),

areas as (
    select issue_dlt_id, string_agg(distinct label_value, ', ' order by label_value) as areas
    from {{ ref('stg_issue_labels') }}
    where label_dimension in ('area', 'adapter')
    group by 1
)

select
    f.issue_number,
    f.title,
    f.issue_category,
    date_diff('day', f.created_at, a.as_of_date) as age_days,
    date_diff('day', f.updated_at, a.as_of_date) as days_idle,
    f.reactions_total_count as reactions,
    f.comments_total_count as comments,
    f.is_customer_reported,
    f.issue_url,
    f.triage_status,
    f.is_hard_blocker,
    coalesce(ar.areas, '') as areas
from {{ ref('fct_issues') }} f
cross join a
left join areas ar using (issue_dlt_id)
where f.state = 'OPEN' and f.issue_category != 'epic'
order by f.reactions_total_count desc, f.comments_total_count desc, f.created_at
limit 25
