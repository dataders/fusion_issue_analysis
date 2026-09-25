{#
  Q: How close is each open epic to done?
  Open epics with at least one sub-issue, most complete first — the top of
  the list is what can be closed out soon.
#}
select
    epic_number,
    title,
    epic_url as issue_url,
    child_total,
    child_closed,
    child_open,
    round(100.0 * child_closed / child_total, 0) as pct_complete,
    coalesce(milestone_title, '') as milestone_title
from {{ ref('fct_epics') }}
where state = 'OPEN' and child_total > 0
order by pct_complete desc, child_open, epic_number
