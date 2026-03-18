from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


# ── Data models ──────────────────────────────────────────────────────


class Department(BaseModel):
    id: str
    name: str
    code: str
    parent_id: Optional[str] = None
    is_active: bool = True


class Position(BaseModel):
    id: str
    name: str
    grade: str


class Employee(BaseModel):
    id: str
    employee_code: str
    full_name: str
    email: str
    department_id: str
    position_id: str
    manager_id: Optional[str] = None
    hire_date: Optional[date] = None
    is_active: bool = True


class Document(BaseModel):
    doc_id: str
    doc_type: str
    title: str
    content: str
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    owner_department_id: Optional[str] = None
    department_scope: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    version: str = "1.0"
    is_active: bool = True


class Goal(BaseModel):
    id: str
    employee_id: str
    department_id: str = ""
    position: str = ""
    title: str
    goal_text: str = ""
    description: str = ""
    metric: str = ""
    deadline: Optional[date] = None
    status: str = "draft"
    quarter: str = ""
    year: int = 0
    weight: Optional[float] = None
    reviewer_comment: str = ""
    created_at: str = ""
    updated_at: str = ""


# ── §4.2 Extended data models (hackathon dump) ──────────────────────


class Project(BaseModel):
    id: str
    name: str
    status: str = "active"
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class System(BaseModel):
    id: str
    name: str
    system_type: str = ""


class EmployeeProject(BaseModel):
    employee_id: str
    project_id: str
    role: str = ""
    allocation_percent: float = 0.0
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class GoalEvent(BaseModel):
    id: str
    goal_id: str
    event_type: str = ""
    actor_id: str = ""
    old_status: str = ""
    new_status: str = ""
    old_text: str = ""
    new_text: str = ""
    metadata: str = ""
    created_at: str = ""


class GoalReview(BaseModel):
    id: str
    goal_id: str
    reviewer_id: str = ""
    verdict: str = ""
    comment_text: str = ""
    created_at: str = ""


class KpiCatalog(BaseModel):
    id: str
    name: str
    unit: str = ""
    description: str = ""


class KpiTimeseries(BaseModel):
    id: str
    kpi_id: str
    department_id: str = ""
    period: str = ""
    value: float = 0.0


# ── Request schemas ──────────────────────────────────────────────────


class EvaluateGoalRequest(BaseModel):
    employee_id: str
    goal_text: str
    quarter: str
    year: int


class RewriteGoalRequest(BaseModel):
    employee_id: str
    goal_text: str
    quarter: str


class GenerateGoalsRequest(BaseModel):
    employee_id: str
    quarter: str
    year: int
    count: int = 3
    focus: Optional[str] = None


class BatchGoalItem(BaseModel):
    title: str
    weight: Optional[float] = None


class EvaluateBatchRequest(BaseModel):
    employee_id: str
    quarter: str
    year: int
    goals: list[BatchGoalItem]


class IngestDocumentsRequest(BaseModel):
    documents: list[Document]


# ── Response schemas ─────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    mode: str = "demo"
    vector_backend: str = "memory"
    indexed_documents: int = 0
    indexed_chunks: int = 0
    llm_enabled: bool = False
    employees_count: int = 0
    goals_count: int = 0
    goal_events_count: int = 0
    goal_reviews_count: int = 0
    kpi_catalog_count: int = 0


class SmartBreakdown(BaseModel):
    specific: float
    measurable: float
    achievable: float
    relevant: float
    timebound: float


class SourceEvidence(BaseModel):
    doc_id: str
    title: str
    doc_type: str
    fragment: str
    score: float = 0.0


class OkrMapping(BaseModel):
    objective: str = ""
    key_results: list[str] = Field(default_factory=list)
    ambition_score: float = 0.0
    transparency_score: float = 0.0
    okr_recommendation: str = ""


class GoalEvaluationResponse(BaseModel):
    scores: SmartBreakdown
    overall_score: float
    alignment_level: str
    goal_type: str
    methodology: str = "SMART+OKR"
    recommendations: list[str] = Field(default_factory=list)
    rewrite: str = ""
    source: Optional[SourceEvidence] = None
    achievability: Optional["AchievabilityCheck"] = None
    okr_mapping: Optional[OkrMapping] = None


class GeneratedGoal(BaseModel):
    title: str
    score: float
    alignment_level: str
    goal_type: str
    methodology: str = "SMART+OKR"
    rationale: str = ""
    source: Optional[SourceEvidence] = None


class BatchItemResult(BaseModel):
    title: str
    weight: Optional[float] = None
    overall_score: float
    alignment_level: str
    goal_type: str
    duplicate_of: Optional[int] = None


class BatchEvaluationResponse(BaseModel):
    goal_count: int
    average_smart_index: float
    strategic_goal_share: float
    total_weight: Optional[float] = None
    weakest_criteria: list[str] = Field(default_factory=list)
    duplicates_found: int = 0
    alerts: list[str] = Field(default_factory=list)
    items: list[BatchItemResult] = Field(default_factory=list)


class DepartmentSnapshot(BaseModel):
    department_id: str
    department_name: str
    avg_smart_score: float = 0.0
    strategic_goal_share: float = 0.0
    weakest_criterion: str = "n/a"
    alert_count: int = 0
    maturity_index: float = 0.0
    maturity_level: str = "начальный"


class DashboardOverview(BaseModel):
    quarter: str
    year: int
    total_departments: int = 0
    total_goals_evaluated: int = 0
    avg_smart_score: float = 0.0
    strategic_goal_share: float = 0.0
    departments: list[DepartmentSnapshot] = Field(default_factory=list)


class EmployeeContextResponse(BaseModel):
    employee: Employee
    department: Optional[Department] = None
    position: Optional[Position] = None
    manager: Optional[Employee] = None
    active_goals: list[Goal] = Field(default_factory=list)
    projects: list[dict] = Field(default_factory=list)
    department_kpis: list[dict] = Field(default_factory=list)
    goal_history_stats: dict = Field(default_factory=dict)


class IngestDocumentsResponse(BaseModel):
    indexed_documents: int
    indexed_chunks: int


# ── F-14: Cascade goals ─────────────────────────────────────────────


class CascadeGoalsRequest(BaseModel):
    manager_id: str
    quarter: str
    year: int
    count_per_employee: int = 3
    focus: Optional[str] = None


class CascadeEmployeeGoals(BaseModel):
    employee_id: str
    employee_name: str
    position: str
    department: str
    goals: list["GeneratedGoal"] = Field(default_factory=list)


class CascadeGoalsResponse(BaseModel):
    manager_id: str
    manager_name: str
    manager_goals: list[Goal] = Field(default_factory=list)
    subordinates: list[CascadeEmployeeGoals] = Field(default_factory=list)
    total_generated: int = 0


# ── F-20: Achievability check ───────────────────────────────────────


class AchievabilityCheck(BaseModel):
    is_achievable: bool = True
    confidence: float = 0.0
    historical_avg_score: Optional[float] = None
    similar_goals_found: int = 0
    warning: Optional[str] = None


# ── F-22: Maturity index ────────────────────────────────────────────


class GoalTypeDistribution(BaseModel):
    impact_based: float = 0.0
    output_based: float = 0.0
    activity_based: float = 0.0


class AlignmentDistribution(BaseModel):
    strategic: float = 0.0
    functional: float = 0.0
    operational: float = 0.0


class SmartDistribution(BaseModel):
    excellent: int = 0       # >= 0.8
    good: int = 0            # 0.6 – 0.79
    needs_improvement: int = 0  # < 0.6


class MaturityReport(BaseModel):
    department_id: str
    department_name: str
    quarter: str
    year: int
    maturity_index: float = 0.0           # 0.0–1.0 integrated index
    maturity_level: str = "начальный"     # начальный / развивающийся / зрелый / продвинутый
    total_employees: int = 0
    employees_with_goals: int = 0
    total_goals: int = 0
    avg_smart_score: float = 0.0
    strategic_goal_share: float = 0.0
    smart_distribution: SmartDistribution = Field(default_factory=SmartDistribution)
    goal_type_distribution: GoalTypeDistribution = Field(default_factory=GoalTypeDistribution)
    alignment_distribution: AlignmentDistribution = Field(default_factory=AlignmentDistribution)
    weakest_criteria: list[str] = Field(default_factory=list)
    top_recommendations: list[str] = Field(default_factory=list)
    alert_count: int = 0


# ── Notifications (Alert Manager) ────────────────────────────────────


class NotificationItem(BaseModel):
    id: str
    severity: str = "warning"  # critical | warning | info
    target_role: str = "manager"  # manager | employee | hr
    employee_id: Optional[str] = None
    employee_name: str = ""
    department_id: str = ""
    department_name: str = ""
    title: str
    message: str
    quarter: str = ""
    year: int = 0


class NotificationsResponse(BaseModel):
    total: int = 0
    critical: int = 0
    warnings: int = 0
    info: int = 0
    items: list[NotificationItem] = Field(default_factory=list)
