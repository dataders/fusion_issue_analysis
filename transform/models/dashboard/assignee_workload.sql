{#
  Q: Who is carrying the open work?
  Top 15 assignees by open non-epic issues, by type. Long format.
  '(unassigned)' is included so the gap is visible.
#}

with open_issues as (
    select issue_dlt_id, issue_category
    from {{ ref('fct_issues') }}
    where state = 'OPEN' and issue_category != 'epic'
),

assigned as (
    select o.issue_category, coalesce(a.assignee_login, '(unassigned)') as assignee_login
    from open_issues o
    left join {{ ref('stg_issue_assignees') }} a using (issue_dlt_id)
),

ranked as (
    select assignee_login, count(*) as total
    from assigned
    group by 1
    order by total desc, assignee_login
    limit 15
)

select
    x.assignee_login,
    x.issue_category,
    count(*) as issue_count,
    r.total as assignee_total
from assigned x
inner join ranked r using (assignee_login)
group by all
order by assignee_total desc, assignee_login, issue_category
