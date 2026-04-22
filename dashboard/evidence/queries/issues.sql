SELECT
    issue_number,
    title,
    state,
    issue_category,
    strftime(created_at, '%Y-%m-%d') as created_date,
    strftime(closed_at, '%Y-%m-%d') as closed_date,
    strftime(updated_at, '%Y-%m-%d') as updated_date,
    hours_to_close,
    hours_to_first_response,
    reactions_total_count,
    comments_total_count,
    milestone_title,
    is_labeled::int as is_labeled,
    is_assigned::int as is_assigned,
    has_milestone::int as has_milestone,
    author_login
FROM fct_issues
ORDER BY issue_number DESC
