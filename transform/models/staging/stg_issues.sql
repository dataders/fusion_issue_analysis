with source as (
    select * from read_parquet('../data/raw/fusion_issues/issues/*.parquet')
),

renamed as (
    select
        _dlt_id as issue_dlt_id,
        number as issue_number,
        url as issue_url,
        title,
        body,
        state,
        closed,
        author__login as author_login,
        author__avatar_url as author_avatar_url,
        author_association,
        milestone__number as milestone_number,
        milestone__title as milestone_title,
        milestone__description as milestone_description,
        milestone__state as milestone_state,
        milestone__due_on as milestone_due_on,
        milestone__created_at as milestone_created_at,
        milestone__closed_at as milestone_closed_at,
        reactions_total_count,
        comments_total_count,
        created_at,
        updated_at,
        closed_at
    from source
)

select * from renamed
