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
)

select * from renamed
