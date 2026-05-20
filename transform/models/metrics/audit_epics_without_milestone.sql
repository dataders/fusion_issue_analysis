select
    epic_number,
    epic_url,
    title,
    state,
    created_at,
    child_total,
    child_open
from {{ ref('fct_epics') }}
where is_orphan_epic
order by created_at
