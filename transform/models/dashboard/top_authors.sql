select
    author_login,
    count(*) as issues_opened
from {{ ref('fct_issues') }}
where author_login is not null
group by author_login
order by issues_opened desc
limit 15
