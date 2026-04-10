select
    il.issue_dlt_id,
    il.label_name,
    i.issue_number,
    i.created_at as issue_created_at,
    i.state as issue_state
from {{ ref('stg_issue_labels') }} il
inner join {{ ref('stg_issues') }} i
    on il.issue_dlt_id = i.issue_dlt_id
