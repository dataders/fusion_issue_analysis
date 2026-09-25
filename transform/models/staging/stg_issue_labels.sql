{#
  One row per (issue, label). dbt-core renamed its labels around Fusion
  (`bug` -> `type:bug`, `triage` -> `status:triage`, ...), and older issues can
  still carry the legacy names, so every label is normalized here into a
  (label_dimension, label_value) pair. Explicit mappings live in the
  `label_map` seed; any other `prefix:value` label splits on the colon.
  Downstream models should filter on label_dimension/label_value, never on
  raw label_name.
#}

with source as (
    select * from {{ raw_source('issues__labels__nodes') }}
),

renamed as (
    select
        _dlt_id as label_dlt_id,
        _dlt_parent_id as issue_dlt_id,
        name as label_name,
        color as label_color,
        description as label_description
    from source
),

label_map as (
    select * from {{ ref('label_map') }}
)

select
    r.*,
    coalesce(
        m.dimension,
        case when r.label_name like '%:%' then split_part(r.label_name, ':', 1) end,
        'other'
    ) as label_dimension,
    coalesce(
        m.value,
        case when r.label_name like '%:%' then split_part(r.label_name, ':', 2) end,
        r.label_name
    ) as label_value
from renamed r
left join label_map m on r.label_name = m.label_name
