export type SummaryKpis = {
  opened_4w: number;
  closed_4w: number;
  open_issues: number;
  total_issues: number;
  rolling_median_close_days: number;
  pct_responded_48h: number;
  stale_count: number;
};

export type TriageHealth = {
  total_open: number;
  pct_labeled: number;
  pct_assigned: number;
  pct_milestoned: number;
  pct_typed: number;
  unlabeled_count: number;
  unassigned_count: number;
};

export type WeeklyFlow = { week: string; opened: number; closed: number };
export type CategoryRow = { issue_category: string; state: string; n: number };
export type ResponsePctile = { week: string; p25: number; p50: number; p75: number };
export type PriorityRow = {
  issue_number: number;
  title: string;
  issue_category: string;
  reactions_total_count: number;
  comments_total_count: number;
  age_days: number;
  url: string;
};

export type DashboardData = {
  summary_kpis: SummaryKpis;
  triage_health: TriageHealth;
  weekly_flow: WeeklyFlow[];
  categories: CategoryRow[];
  response_pctiles: ResponsePctile[];
  community_priorities: PriorityRow[];
};
