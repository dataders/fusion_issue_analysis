with issue_authors as (
    select distinct
        author_login as login,
        author_avatar_url as avatar_url
    from {{ ref('stg_issues') }}
    where author_login is not null
),

comment_authors as (
    select distinct
        author_login as login,
        author_avatar_url as avatar_url
    from {{ ref('stg_issue_comments') }}
    where author_login is not null
),

assignees as (
    select distinct
        assignee_login as login,
        assignee_avatar_url as avatar_url
    from {{ ref('stg_issue_assignees') }}
    where assignee_login is not null
),

all_users as (
    select * from issue_authors
    union
    select * from comment_authors
    union
    select * from assignees
)

select
    login,
    avatar_url
from all_users
