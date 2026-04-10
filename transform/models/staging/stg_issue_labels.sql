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
)

select * from renamed
