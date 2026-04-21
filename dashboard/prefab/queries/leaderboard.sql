select author_login, count(*) as issues_closed
from fct_issues
where state = 'CLOSED' and issue_category != 'epic'
group by author_login
order by issues_closed desc
limit 15
