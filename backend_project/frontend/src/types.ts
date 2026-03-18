/* ── Data models ─────────────────────────────────────────────────── */

export interface Department {
  id: string;
  name: string;
  code: string;
  parent_id?: string | null;
  is_active?: boolean;
}

export interface Position {
  id: string;
  name: string;
  grade: string;
}

export interface Employee {
  id: string;
  employee_code: string;
  full_name: string;
  email: string;
  department_id: string;
  position_id: string;
  manager_id?: string | null;
  hire_date?: string | null;
  is_active?: boolean;
}

export interface Goal {
  id: string;
  employee_id: string;
  title: string;
  description?: string;
  status?: string;
  quarter?: string;
  year?: number;
  weight?: number | null;
  created_at?: string;
  updated_at?: string;
}

export interface Document {
  doc_id: string;
  doc_type: string;
  title: string;
  content: string;
  valid_from?: string | null;
  valid_to?: string | null;
  owner_department_id?: string | null;
  department_scope?: string[];
  keywords?: string[];
  version?: string;
  is_active?: boolean;
}

/* ── Response types ──────────────────────────────────────────────── */

export interface HealthResponse {
  status: string;
  mode: string;
  vector_backend: string;
  indexed_documents: number;
  indexed_chunks: number;
  llm_enabled: boolean;
  employees_count?: number;
  goals_count?: number;
  goal_events_count?: number;
  goal_reviews_count?: number;
  kpi_catalog_count?: number;
}

/* ── Reference data (for dropdowns) ──────────────────────────────── */

export interface DepartmentRef {
  id: string;
  name: string;
  code: string;
}

export interface EmployeeRef {
  id: string;
  full_name: string;
  department_id: string;
  department_name: string;
  position_id: string;
  position_name: string;
  manager_id?: string | null;
}

export interface DataStats {
  departments: number;
  positions: number;
  employees: number;
  documents: number;
  goals: number;
  goal_events: number;
  goal_reviews: number;
  kpi_catalog: number;
  kpi_timeseries: number;
  has_dump_data: boolean;
}

export interface GoalHistoryResponse {
  goal_id: string;
  events: Record<string, unknown>[];
  reviews: Record<string, unknown>[];
  total_events: number;
  total_reviews: number;
}

export interface SmartBreakdown {
  specific: number;
  measurable: number;
  achievable: number;
  relevant: number;
  timebound: number;
}

export interface SourceEvidence {
  doc_id: string;
  title: string;
  doc_type: string;
  fragment: string;
  score?: number;
}

export interface AchievabilityCheck {
  is_achievable: boolean;
  confidence: number;
  historical_avg_score?: number | null;
  similar_goals_found: number;
  warning?: string | null;
}

export interface OkrMapping {
  objective: string;
  key_results: string[];
  ambition_score: number;
  transparency_score: number;
  okr_recommendation: string;
}

export interface GoalEvaluationResponse {
  scores: SmartBreakdown;
  overall_score: number;
  alignment_level: string;
  goal_type: string;
  methodology: string;
  recommendations: string[];
  rewrite: string;
  source?: SourceEvidence | null;
  achievability?: AchievabilityCheck | null;
  okr_mapping?: OkrMapping | null;
}

export interface GeneratedGoal {
  title: string;
  score: number;
  alignment_level: string;
  goal_type: string;
  methodology: string;
  rationale: string;
  source: SourceEvidence;
}

export interface BatchItemResult {
  title: string;
  weight?: number | null;
  overall_score: number;
  alignment_level: string;
  goal_type: string;
  duplicate_of?: number | null;
}

export interface BatchEvaluationResponse {
  goal_count: number;
  average_smart_index: number;
  strategic_goal_share: number;
  total_weight?: number | null;
  weakest_criteria: string[];
  duplicates_found: number;
  alerts: string[];
  items: BatchItemResult[];
}

export interface DepartmentSnapshot {
  department_id: string;
  department_name: string;
  avg_smart_score: number;
  strategic_goal_share: number;
  weakest_criterion: string;
  alert_count: number;
  maturity_index: number;
  maturity_level: string;
}

export interface DashboardOverview {
  quarter: string;
  year: number;
  total_departments: number;
  total_goals_evaluated: number;
  avg_smart_score: number;
  strategic_goal_share: number;
  departments: DepartmentSnapshot[];
}

export interface EmployeeContextResponse {
  employee: Employee;
  department?: Department | null;
  position?: Position | null;
  manager?: Employee | null;
  active_goals: Goal[];
}

/* ── F-14 Cascade ────────────────────────────────────────────────── */

export interface CascadeEmployeeGoals {
  employee_id: string;
  employee_name: string;
  position: string;
  department: string;
  goals: GeneratedGoal[];
}

export interface CascadeGoalsResponse {
  manager_id: string;
  manager_name: string;
  manager_goals: Goal[];
  subordinates: CascadeEmployeeGoals[];
  total_generated: number;
}

/* ── F-22 Maturity ───────────────────────────────────────────────── */

export interface GoalTypeDistribution {
  impact_based: number;
  output_based: number;
  activity_based: number;
}

export interface AlignmentDistribution {
  strategic: number;
  functional: number;
  operational: number;
}

export interface SmartDistribution {
  excellent: number;
  good: number;
  needs_improvement: number;
}

export interface MaturityReport {
  department_id: string;
  department_name: string;
  quarter: string;
  year: number;
  maturity_index: number;
  maturity_level: string;
  total_employees: number;
  employees_with_goals: number;
  total_goals: number;
  avg_smart_score: number;
  strategic_goal_share: number;
  smart_distribution: SmartDistribution;
  goal_type_distribution: GoalTypeDistribution;
  alignment_distribution: AlignmentDistribution;
  weakest_criteria: string[];
  top_recommendations: string[];
  alert_count: number;
}

/* ── Notifications (Alert Manager) ──────────────────────────────── */

export interface NotificationItem {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  target_role: 'manager' | 'employee' | 'hr';
  employee_id?: string | null;
  employee_name: string;
  department_id: string;
  department_name: string;
  title: string;
  message: string;
  quarter: string;
  year: number;
}

export interface NotificationsResponse {
  total: number;
  critical: number;
  warnings: number;
  info: number;
  items: NotificationItem[];
}
