with source as (
    select * from {{ raw_source('issues') }}
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
        issue_type__name as issue_type,
        milestone__number as milestone_number,
        reactions_total_count,
        comments_total_count,
        created_at,
        updated_at,
        closed_at,
        issue_type__name as issue_type,
        parent__number as parent_number,
        parent__title as parent_title,
        parent__issue_type__name as parent_issue_type
    from source
)

select * from renamed
