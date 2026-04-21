SELECT
    strftime(date_day, '%Y-%m-%d') as date_day,
    milestone_title,
    open_at_date
FROM milestone_burndown
WHERE date_day::date = date_trunc('week', date_day::date)
  AND milestone_title IN (
      SELECT DISTINCT milestone_title
      FROM dim_milestones WHERE milestone_state = 'OPEN'
  )
ORDER BY milestone_title, date_day
