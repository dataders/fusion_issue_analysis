# dbt v2 issue health dashboard

Use public GitHub issue data to answer these reader questions:

1. Where do things stand? Show current open issues, 28-day opened and closed counts, awaiting-triage count and age, response within 48 hours, median days to close, and customer-reported open issues.
2. Is the backlog shrinking? Show open issues over time and opened versus closed issues by complete week.
3. Are we keeping up with triage? Show triage status and age, weekly 48-hour response rate, and the oldest untriaged issues.
4. Where is the work? Show open issues by area and adapter.
5. How close are the epics? Show completion progress for open epics.
6. What should we work on, and who is on it? Show most-requested open issues and open issues by assignee.

Give an as-of date. The shared dashboard contract is `dashboard/tiles.yml` in the fusion_issue_analysis repository. This brief asks for content only; dashboard framework styling and interaction may differ.
