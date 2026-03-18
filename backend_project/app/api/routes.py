from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.container import AppContainer, container
from app.models.schemas import (
    CascadeGoalsRequest,
    CascadeGoalsResponse,
    DashboardOverview,
    DepartmentSnapshot,
    EmployeeContextResponse,
    EvaluateBatchRequest,
    EvaluateGoalRequest,
    GenerateGoalsRequest,
    GeneratedGoal,
    GoalEvaluationResponse,
    HealthResponse,
    IngestDocumentsRequest,
    IngestDocumentsResponse,
    MaturityReport,
    RewriteGoalRequest,
)

router = APIRouter()


def get_container() -> AppContainer:
    return container


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health(ctx: AppContainer = Depends(get_container)) -> HealthResponse:
    return ctx.engine.health()


# ── Reference data (for UI dropdowns) ──────────────────────────────


@router.get("/api/v1/departments", tags=["reference"])
async def list_departments(ctx: AppContainer = Depends(get_container)):
    """Return all departments (for dropdown selectors)."""
    depts = ctx.engine.store.list_departments()
    return [{"id": d.id, "name": d.name, "code": d.code} for d in depts]


@router.get("/api/v1/employees", tags=["reference"])
async def list_employees(
    department_id: str | None = Query(None),
    ctx: AppContainer = Depends(get_container),
):
    """Return employees with position/department names (for dropdowns)."""
    emps = ctx.engine.store.list_employees(department_id)
    result = []
    for e in emps:
        dept = ctx.engine.store.get_department(e.department_id)
        pos = ctx.engine.store.get_position(e.position_id)
        result.append({
            "id": e.id,
            "full_name": e.full_name,
            "department_id": e.department_id,
            "department_name": dept.name if dept else "",
            "position_id": e.position_id,
            "position_name": pos.name if pos else "",
            "manager_id": e.manager_id,
        })
    return result


@router.post("/api/v1/goals/evaluate", response_model=GoalEvaluationResponse, tags=["goals"])
async def evaluate_goal(payload: EvaluateGoalRequest, ctx: AppContainer = Depends(get_container)) -> GoalEvaluationResponse:
    try:
        return ctx.engine.evaluate_goal(payload.employee_id, payload.goal_text, payload.quarter, payload.year)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/v1/goals/rewrite", response_model=dict, tags=["goals"])
async def rewrite_goal(payload: RewriteGoalRequest, ctx: AppContainer = Depends(get_container)) -> dict:
    try:
        return {"rewrite": ctx.engine.rewrite_goal(payload.employee_id, payload.goal_text, payload.quarter)}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/v1/goals/generate", response_model=list[GeneratedGoal], tags=["goals"])
async def generate_goals(payload: GenerateGoalsRequest, ctx: AppContainer = Depends(get_container)) -> list[GeneratedGoal]:
    try:
        return ctx.engine.generate_goals(payload.employee_id, payload.quarter, payload.year, payload.count, payload.focus)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/v1/goals/evaluate-batch", tags=["goals"])
async def evaluate_batch(payload: EvaluateBatchRequest, ctx: AppContainer = Depends(get_container)):
    try:
        return ctx.engine.evaluate_batch(payload.employee_id, payload.quarter, payload.year, [item.model_dump() for item in payload.goals])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/v1/dashboard/departments/{department_id}", response_model=DepartmentSnapshot, tags=["dashboard"])
async def dashboard_department(
    department_id: str,
    quarter: str = Query("Q2", pattern=r"^Q[1-4]$"),
    year: int = Query(2026, ge=2024, le=2100),
    ctx: AppContainer = Depends(get_container),
) -> DepartmentSnapshot:
    try:
        return ctx.engine.dashboard_department(department_id, quarter, year)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/v1/dashboard/overview", response_model=DashboardOverview, tags=["dashboard"])
async def dashboard_overview(
    quarter: str = Query("Q2", pattern=r"^Q[1-4]$"),
    year: int = Query(2026, ge=2024, le=2100),
    ctx: AppContainer = Depends(get_container),
) -> DashboardOverview:
    return ctx.engine.dashboard_overview(quarter, year)


@router.post("/api/v1/documents/ingest", response_model=IngestDocumentsResponse, tags=["documents"])
async def ingest_documents(payload: IngestDocumentsRequest, ctx: AppContainer = Depends(get_container)) -> IngestDocumentsResponse:
    return ctx.engine.ingest_documents(payload.documents)


@router.get("/api/v1/employees/{employee_id}/context", response_model=EmployeeContextResponse, tags=["employees"])
async def employee_context(
    employee_id: str,
    quarter: str = Query("Q2", pattern=r"^Q[1-4]$"),
    year: int = Query(2026, ge=2024, le=2100),
    ctx: AppContainer = Depends(get_container),
) -> EmployeeContextResponse:
    try:
        return ctx.engine.employee_context(employee_id, quarter, year)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ── F-14: Cascade goals from manager ────────────────────────────────


@router.post("/api/v1/goals/cascade", response_model=CascadeGoalsResponse, tags=["goals"])
async def cascade_goals(payload: CascadeGoalsRequest, ctx: AppContainer = Depends(get_container)) -> CascadeGoalsResponse:
    try:
        return ctx.engine.cascade_goals(
            payload.manager_id,
            payload.quarter,
            payload.year,
            payload.count_per_employee,
            payload.focus,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ── F-22: Maturity report ───────────────────────────────────────────


@router.get("/api/v1/dashboard/departments/{department_id}/maturity", response_model=MaturityReport, tags=["dashboard"])
async def department_maturity(
    department_id: str,
    quarter: str = Query("Q2", pattern=r"^Q[1-4]$"),
    year: int = Query(2026, ge=2024, le=2100),
    ctx: AppContainer = Depends(get_container),
) -> MaturityReport:
    try:
        return ctx.engine.maturity_report(department_id, quarter, year)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ── F-15: Goal history / versioning ─────────────────────────────────


@router.get("/api/v1/goals/{goal_id}/history", tags=["goals"])
async def goal_history(goal_id: str, ctx: AppContainer = Depends(get_container)):
    """Return change history for a goal (events + reviews). §3.2.1 F-15."""
    try:
        events = ctx.engine.store.list_goal_events(goal_id)
        reviews = ctx.engine.store.list_goal_reviews(goal_id)
        return {
            "goal_id": goal_id,
            "events": [e.model_dump() for e in events],
            "reviews": [r.model_dump() for r in reviews],
            "total_events": len(events),
            "total_reviews": len(reviews),
        }
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ── Alert Manager: Notifications endpoint ────────────────────────────


@router.get("/api/v1/notifications", tags=["notifications"])
async def list_notifications(
    quarter: str = Query("Q2", pattern=r"^Q[1-4]$"),
    year: int = Query(2026, ge=2020, le=2099),
    ctx: AppContainer = Depends(get_container),
):
    """Return generated notifications / alerts for managers, employees and HR."""
    try:
        return ctx.engine.notifications(quarter, year)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── §4.2: Data stats endpoint ───────────────────────────────────────


@router.get("/api/v1/data/stats", tags=["system"])
async def data_stats(ctx: AppContainer = Depends(get_container)):
    """Return counts for all tables — useful for verifying dump load."""
    tables = [
        "departments", "positions", "employees", "documents", "goals",
        "goal_events", "goal_reviews", "kpi_catalog", "kpi_timeseries",
    ]
    stats = {}
    for t in tables:
        try:
            stats[t] = ctx.engine.store.count_table_rows(t)
        except Exception:
            stats[t] = 0
    stats["has_dump_data"] = any(stats.get(k, 0) > 50 for k in ["employees", "goals"])
    return stats
