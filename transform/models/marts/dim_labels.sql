select distinct
    label_name,
    label_color,
    label_description
from {{ ref('stg_issue_labels') }}
