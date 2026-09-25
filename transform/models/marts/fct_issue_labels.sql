select
    il.issue_dlt_id,
    il.label_name,
    il.label_dimension,
    il.label_value,
    i.issue_number,
    i.issue_category,
    i.created_at as issue_created_at,
    i.state as issue_state
from {{ ref('stg_issue_labels') }} il
inner join {{ ref('fct_issues') }} i
    on il.issue_dlt_id = i.issue_dlt_id
