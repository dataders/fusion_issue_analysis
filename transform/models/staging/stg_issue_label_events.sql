{# LABELED_EVENT / UNLABELED_EVENT timeline entries, normalized like stg_issue_labels. #}

with source as (
    select * from {{ raw_source('issues__timeline_items') }}
),

renamed as (
    select
        _dlt_id as event_dlt_id,
        _dlt_parent_id as issue_dlt_id,
        typename as event_type,
        created_at as event_at,
        label__name as label_name,
        label__color as label_color,
        actor__login as actor_login,
        actor__avatar_url as actor_avatar_url,
        actor__url as actor_url
    from source
    where typename in ('LabeledEvent', 'UnlabeledEvent')
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
