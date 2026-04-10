with source as (
    select * from read_parquet('../data/raw/fusion_issues/issues__labels__nodes/*.parquet')
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
