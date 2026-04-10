select
    c.comment_dlt_id,
    c.issue_dlt_id,
    c.comment_id,
    c.comment_url,
    c.body,
    c.author_login,
    c.author_association,
    c.reactions_total_count,
    c.created_at,
    i.issue_number,
    i.title as issue_title
from {{ ref('stg_issue_comments') }} c
inner join {{ ref('stg_issues') }} i
    on c.issue_dlt_id = i.issue_dlt_id
