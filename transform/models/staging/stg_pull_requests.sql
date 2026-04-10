with source as (
    select * from {{ raw_source('pull_requests') }}
),

renamed as (
    select
        _dlt_id as pr_dlt_id,
        number as pr_number,
        url as pr_url,
        title,
        body,
        state,
        closed,
        author__login as author_login,
        author__avatar_url as author_avatar_url,
        author_association,
        reactions_total_count,
        comments_total_count,
        created_at,
        updated_at,
        closed_at
    from source
)

select * from renamed
