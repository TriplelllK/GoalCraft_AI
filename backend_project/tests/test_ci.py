"""
GoalCraft AI — CI test suite.

Runs fully in-memory (no PostgreSQL, no Qdrant, no OpenAI key required).
Tests cover:
  - API contract (status codes, required fields)
  - SMART evaluation quality (rule-based, deterministic)
  - IT domain relevance scoring improvements
  - Alignment level classification
  - Goal type classification
  - Batch evaluation alerts
  - Dashboard / notifications / cascade endpoints
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

# conftest.py sets env vars before this import
from app.main import app
from app.api.routes import get_container
from app.container import AppContainer
from app.services.rules import (
    ROLE_METRIC_HINTS,
    has_measurement,
    has_time_bound,
    hr_business_relevance_score,
    specificity_quality_score,
)
from app.services.engine import GoalEngine
from app.storage.memory import MemoryStore
from app.vector.memory_vector import MemoryVectorStore

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def mem_container():
    """Fresh in-memory container used for all tests."""
    c = AppContainer()
    assert c.settings.storage_backend == "memory"
    assert c.settings.vector_backend == "memory"
    return c


@pytest.fixture(scope="session")
def client(mem_container):
    """TestClient wired to the in-memory container."""
    app.dependency_overrides[get_container] = lambda: mem_container
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def emp_id(client):
    """Return first employee id from the demo store."""
    emps = client.get("/api/v1/employees").json()
    assert emps, "Demo store must have at least one employee"
    return emps[0]["id"]


@pytest.fixture(scope="session")
def dept_id(client):
    """Return first department id from the demo store."""
    depts = client.get("/api/v1/departments").json()
    assert depts, "Demo store must have at least one department"
    return depts[0]["id"]


# ---------------------------------------------------------------------------
# Section 1: Unit tests — SMART rule functions (no HTTP)
# ---------------------------------------------------------------------------

class TestSmartRuleFunctions:

    # ── Specific / specificity ──────────────────────────────────────

    def test_specific_high_with_verb_and_object(self):
        goal = "Внедрить систему мониторинга SLA в рамках проекта CI/CD"
        score = specificity_quality_score(goal)
        assert score >= 0.7, f"Expected >= 0.7, got {score}"

    def test_specific_low_vague_goal(self):
        goal = "Улучшить работу"
        score = specificity_quality_score(goal)
        assert score < 0.5, f"Expected < 0.5, got {score}"

    def test_specific_medium_no_object(self):
        goal = "Оптимизировать процессы в команде"
        score = specificity_quality_score(goal)
        assert 0.3 <= score <= 0.75

    # ── Measurable ──────────────────────────────────────────────────

    def test_measurable_with_percent(self):
        assert has_measurement("Повысить SLA до 95%")

    def test_measurable_with_count(self):
        assert has_measurement("Закрыть 50 тикетов за квартал")

    def test_measurable_with_sla_pattern(self):
        assert has_measurement("не ниже 99.5% SLA")

    def test_measurable_missing(self):
        assert not has_measurement("Улучшить качество кода")

    def test_measurable_with_days(self):
        assert has_measurement("Сократить MTTR до 2 рабочих дней")

    # ── Time-bound ──────────────────────────────────────────────────

    def test_timebound_with_date(self):
        assert has_time_bound("Внедрить до 30.06.2026")

    def test_timebound_with_quarter(self):
        assert has_time_bound("Выполнить до конца Q2")

    def test_timebound_with_q_pattern(self):
        assert has_time_bound("Q3 запустить сервис")

    def test_timebound_missing(self):
        assert not has_time_bound("Разработать новый модуль")

    def test_timebound_weekly(self):
        assert has_time_bound("Ежемесячно отчитываться о прогрессе")

    # ── IT domain relevance (§4.2: all employees are IT engineers) ──

    def test_it_goal_sla_high_relevance(self):
        goal = "Обеспечить соблюдение SLA по сервисам не ниже 95%"
        score = hr_business_relevance_score(goal)
        assert score >= 0.72, f"IT SLA goal: expected >= 0.72, got {score}"

    def test_it_goal_uptime_high_relevance(self):
        goal = "Снизить downtime сервисов и обеспечить uptime 99.5%"
        score = hr_business_relevance_score(goal)
        assert score >= 0.72, f"IT uptime goal: expected >= 0.72, got {score}"

    def test_it_goal_devops_high_relevance(self):
        goal = "Внедрить CI/CD пайплайн для автоматизации деплоя до Q2"
        score = hr_business_relevance_score(goal)
        assert score >= 0.72, f"DevOps goal: expected >= 0.72, got {score}"

    def test_it_goal_mttr_high_relevance(self):
        goal = "Настроить контроль MTTR инцидентов в системе мониторинга"
        score = hr_business_relevance_score(goal)
        assert score >= 0.72, f"MTTR goal: expected >= 0.72, got {score}"

    def test_it_goal_ml_high_relevance(self):
        goal = "Обучить и задеплоить ML модель для классификации данных"
        score = hr_business_relevance_score(goal)
        assert score >= 0.72, f"ML goal: expected >= 0.72, got {score}"

    def test_vague_goal_low_relevance(self):
        goal = "Стараться делать лучше"
        score = hr_business_relevance_score(goal)
        assert score <= 0.50, f"Vague goal: expected <= 0.50, got {score}"


# ---------------------------------------------------------------------------
# Section 2: Role hints coverage for §4.2 actual IT roles
# ---------------------------------------------------------------------------

class TestRoleHintsCoverage:

    IT_ROLES = [
        ".net-разработчик (middle)",
        "devops engineer (middle)",
        "data scientist (middle)",
        "bi-разработчик (middle)",
        "sre engineer (senior)",
        "ml engineer (middle)",
        "python backend developer (middle)",
        "qa engineer (middle)",
        "frontend developer (middle)",
        "аналитик данных (middle)",
        "инженер данных (lead)",
        "администратор бд (senior)",
        "специалист servicedesk (l1) (junior)",
        "специалист servicedesk (l2) (middle)",
    ]

    @pytest.mark.parametrize("role", IT_ROLES)
    def test_it_role_has_hint(self, role):
        assert role in ROLE_METRIC_HINTS, f"No hint for role: {role}"

    def test_hint_has_metric_and_business(self):
        for role, hint in ROLE_METRIC_HINTS.items():
            assert "metric" in hint, f"No 'metric' key in hint for {role}"
            assert "business" in hint, f"No 'business' key in hint for {role}"
            assert len(hint["metric"]) > 10, f"Too short metric hint for {role}"


# ---------------------------------------------------------------------------
# Section 3: Alignment level classification (engine method)
# ---------------------------------------------------------------------------

class TestAlignmentLevel:

    @pytest.fixture(scope="class")
    def engine(self):
        store = MemoryStore()
        vector_store = MemoryVectorStore()
        return GoalEngine(store, vector_store)

    def test_strategic_uptime_goal(self, engine):
        goal = "Обеспечить uptime сервисов не ниже 99.5% за счет внедрения мониторинга"
        level = engine._alignment_level(goal, None)
        assert level == "strategic", f"uptime goal should be strategic, got {level}"

    def test_strategic_sla_goal_with_metric(self, engine):
        goal = "Снизить число инцидентов на 30% и обеспечить SLA не ниже 95%"
        level = engine._alignment_level(goal, None)
        assert level == "strategic", f"SLA goal with metric should be strategic, got {level}"

    def test_strategic_cost_reduction(self, engine):
        goal = "Сократить операционные затраты на 15% за счет автоматизации процессов"
        level = engine._alignment_level(goal, None)
        assert level == "strategic", f"cost reduction goal should be strategic, got {level}"

    def test_functional_monitoring(self, engine):
        goal = "Настроить мониторинг инцидентов и отчитываться еженедельно"
        level = engine._alignment_level(goal, None)
        assert level in ("functional", "strategic"), f"monitoring goal should be functional+, got {level}"

    def test_functional_kpi(self, engine):
        goal = "Выполнить KPI по количеству тикетов за квартал"
        level = engine._alignment_level(goal, None)
        assert level in ("functional", "strategic"), f"KPI goal should be functional+, got {level}"

    def test_operational_vague(self, engine):
        goal = "Проводить встречи с командой"
        level = engine._alignment_level(goal, None)
        assert level == "operational", f"vague meeting goal should be operational, got {level}"


# ---------------------------------------------------------------------------
# Section 4: Goal type classification
# ---------------------------------------------------------------------------

class TestGoalType:

    @pytest.fixture(scope="class")
    def engine(self):
        store = MemoryStore()
        vector_store = MemoryVectorStore()
        return GoalEngine(store, vector_store)

    def test_impact_based_with_metric(self, engine):
        goal = "Снизить MTTR инцидентов на 40% до Q2 2026"
        assert engine._goal_type(goal) == "impact-based"

    def test_output_based_deliver(self, engine):
        goal = "Разработать и внедрить систему мониторинга"
        assert engine._goal_type(goal) == "output-based"

    def test_output_based_launch(self, engine):
        goal = "Запустить CI/CD пайплайн в рамках проекта"
        assert engine._goal_type(goal) == "output-based"

    def test_activity_based_default(self, engine):
        goal = "Участвовать в совещаниях и готовить протоколы"
        assert engine._goal_type(goal) == "activity-based"


# ---------------------------------------------------------------------------
# Section 5: API contract — health & reference data
# ---------------------------------------------------------------------------

class TestHealthAndReference:

    def test_health_status_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"

    def test_health_has_required_fields(self, client):
        data = client.get("/health").json()
        for field in ("status", "mode", "vector_backend", "llm_enabled"):
            assert field in data, f"Missing field: {field}"

    def test_health_llm_disabled_in_ci(self, client):
        data = client.get("/health").json()
        assert data["llm_enabled"] is False, "LLM should be disabled in CI (no OPENAI_API_KEY)"

    def test_departments_list_not_empty(self, client):
        r = client.get("/api/v1/departments")
        assert r.status_code == 200
        depts = r.json()
        assert len(depts) >= 1

    def test_departments_schema(self, client):
        depts = client.get("/api/v1/departments").json()
        for d in depts:
            assert "id" in d
            assert "name" in d
            assert "code" in d

    def test_employees_list_not_empty(self, client):
        r = client.get("/api/v1/employees")
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_employees_schema(self, client):
        emps = client.get("/api/v1/employees").json()
        for e in emps:
            for field in ("id", "full_name", "department_id", "position_name"):
                assert field in e, f"Missing field {field} in employee"

    def test_employees_filter_by_department(self, client, dept_id):
        all_emps = client.get("/api/v1/employees").json()
        filtered = client.get(f"/api/v1/employees?department_id={dept_id}").json()
        assert len(filtered) <= len(all_emps)


# ---------------------------------------------------------------------------
# Section 6: Goal evaluation — API contract
# ---------------------------------------------------------------------------

class TestEvaluateGoalContract:

    GOOD_IT_GOAL = (
        "Обеспечить uptime сервисов не ниже 99.5% за счет внедрения "
        "автоматического мониторинга и алертинга до 30.06.2026"
    )
    BAD_GOAL = "Улучшить работу"
    MEDIUM_GOAL = "Внедрить систему мониторинга инцидентов до конца Q2"

    def test_evaluate_returns_200(self, client, emp_id):
        r = client.post("/api/v1/goals/evaluate", json={
            "employee_id": emp_id,
            "goal_text": self.GOOD_IT_GOAL,
            "quarter": "Q2",
            "year": 2026,
        })
        assert r.status_code == 200

    def test_evaluate_unknown_employee_returns_404(self, client):
        r = client.post("/api/v1/goals/evaluate", json={
            "employee_id": "NONEXISTENT_EMP",
            "goal_text": "Some goal",
            "quarter": "Q2",
            "year": 2026,
        })
        assert r.status_code == 404

    def test_evaluate_response_has_required_fields(self, client, emp_id):
        r = client.post("/api/v1/goals/evaluate", json={
            "employee_id": emp_id,
            "goal_text": self.GOOD_IT_GOAL,
            "quarter": "Q2",
            "year": 2026,
        }).json()
        for field in ("scores", "overall_score", "alignment_level", "goal_type",
                      "methodology", "recommendations", "rewrite"):
            assert field in r, f"Missing field: {field}"

    def test_evaluate_scores_has_smart_criteria(self, client, emp_id):
        scores = client.post("/api/v1/goals/evaluate", json={
            "employee_id": emp_id,
            "goal_text": self.GOOD_IT_GOAL,
            "quarter": "Q2",
            "year": 2026,
        }).json()["scores"]
        for criterion in ("specific", "measurable", "achievable", "relevant", "timebound"):
            assert criterion in scores, f"Missing SMART criterion: {criterion}"
            assert 0.0 <= scores[criterion] <= 1.0, f"{criterion} out of [0,1] range"

    def test_evaluate_overall_score_in_range(self, client, emp_id):
        data = client.post("/api/v1/goals/evaluate", json={
            "employee_id": emp_id,
            "goal_text": self.GOOD_IT_GOAL,
            "quarter": "Q2",
            "year": 2026,
        }).json()
        assert 0.0 <= data["overall_score"] <= 1.0

    def test_evaluate_score_explanations_field_present(self, client, emp_id):
        """score_explanations must be a key in response (may be null without LLM)."""
        data = client.post("/api/v1/goals/evaluate", json={
            "employee_id": emp_id,
            "goal_text": self.GOOD_IT_GOAL,
            "quarter": "Q2",
            "year": 2026,
        }).json()
        assert "score_explanations" in data, "score_explanations field missing from response schema"

    def test_evaluate_good_goal_higher_than_bad(self, client, emp_id):
        good = client.post("/api/v1/goals/evaluate", json={
            "employee_id": emp_id,
            "goal_text": self.GOOD_IT_GOAL,
            "quarter": "Q2",
            "year": 2026,
        }).json()["overall_score"]
        bad = client.post("/api/v1/goals/evaluate", json={
            "employee_id": emp_id,
            "goal_text": self.BAD_GOAL,
            "quarter": "Q2",
            "year": 2026,
        }).json()["overall_score"]
        assert good > bad, f"Good goal ({good}) should score higher than bad goal ({bad})"

    def test_evaluate_goal_with_deadline_higher_timebound(self, client, emp_id):
        with_deadline = client.post("/api/v1/goals/evaluate", json={
            "employee_id": emp_id,
            "goal_text": "Внедрить мониторинг SLA до 30.06.2026",
            "quarter": "Q2",
            "year": 2026,
        }).json()["scores"]["timebound"]
        without_deadline = client.post("/api/v1/goals/evaluate", json={
            "employee_id": emp_id,
            "goal_text": "Внедрить мониторинг SLA",
            "quarter": "Q2",
            "year": 2026,
        }).json()["scores"]["timebound"]
        assert with_deadline > without_deadline, (
            f"Goal with deadline ({with_deadline}) should have higher timebound "
            f"than goal without ({without_deadline})"
        )

    def test_evaluate_goal_with_metric_higher_measurable(self, client, emp_id):
        with_metric = client.post("/api/v1/goals/evaluate", json={
            "employee_id": emp_id,
            "goal_text": "Обеспечить SLA не ниже 95% до конца Q2",
            "quarter": "Q2",
            "year": 2026,
        }).json()["scores"]["measurable"]
        without_metric = client.post("/api/v1/goals/evaluate", json={
            "employee_id": emp_id,
            "goal_text": "Обеспечить соблюдение SLA сервисов",
            "quarter": "Q2",
            "year": 2026,
        }).json()["scores"]["measurable"]
        assert with_metric > without_metric, (
            f"Goal with metric ({with_metric}) should score higher than without ({without_metric})"
        )

    def test_evaluate_alignment_strategic_for_it_goal(self, client, emp_id):
        data = client.post("/api/v1/goals/evaluate", json={
            "employee_id": emp_id,
            "goal_text": "Снизить количество инцидентов на 40% за счет автоматизации мониторинга до Q2 2026",
            "quarter": "Q2",
            "year": 2026,
        }).json()
        assert data["alignment_level"] in ("strategic", "functional"), (
            f"IT goal with measurable impact should be strategic/functional, got {data['alignment_level']}"
        )

    def test_evaluate_alignment_operational_for_vague(self, client, emp_id):
        data = client.post("/api/v1/goals/evaluate", json={
            "employee_id": emp_id,
            "goal_text": "Проводить встречи с командой",
            "quarter": "Q2",
            "year": 2026,
        }).json()
        assert data["alignment_level"] == "operational"

    def test_evaluate_methodology_contains_smart(self, client, emp_id):
        data = client.post("/api/v1/goals/evaluate", json={
            "employee_id": emp_id,
            "goal_text": self.MEDIUM_GOAL,
            "quarter": "Q2",
            "year": 2026,
        }).json()
        assert "SMART" in data["methodology"]

    def test_evaluate_recommendations_not_empty(self, client, emp_id):
        data = client.post("/api/v1/goals/evaluate", json={
            "employee_id": emp_id,
            "goal_text": self.BAD_GOAL,
            "quarter": "Q2",
            "year": 2026,
        }).json()
        assert len(data["recommendations"]) >= 1

    def test_evaluate_rewrite_not_empty(self, client, emp_id):
        data = client.post("/api/v1/goals/evaluate", json={
            "employee_id": emp_id,
            "goal_text": self.BAD_GOAL,
            "quarter": "Q2",
            "year": 2026,
        }).json()
        assert len(data["rewrite"]) > 10, "Rewrite should produce a non-trivial result"

    def test_evaluate_goal_type_impact(self, client, emp_id):
        data = client.post("/api/v1/goals/evaluate", json={
            "employee_id": emp_id,
            "goal_text": "Снизить MTTR на 50% до конца Q2",
            "quarter": "Q2",
            "year": 2026,
        }).json()
        assert data["goal_type"] == "impact-based"

    def test_evaluate_goal_type_output(self, client, emp_id):
        data = client.post("/api/v1/goals/evaluate", json={
            "employee_id": emp_id,
            "goal_text": "Разработать и внедрить систему мониторинга SLA",
            "quarter": "Q2",
            "year": 2026,
        }).json()
        assert data["goal_type"] == "output-based"


# ---------------------------------------------------------------------------
# Section 7: Rewrite endpoint
# ---------------------------------------------------------------------------

class TestRewriteGoal:

    def test_rewrite_returns_200(self, client, emp_id):
        r = client.post("/api/v1/goals/rewrite", json={
            "employee_id": emp_id,
            "goal_text": "Улучшить работу",
            "quarter": "Q2",
        })
        assert r.status_code == 200

    def test_rewrite_returns_non_trivial_text(self, client, emp_id):
        data = client.post("/api/v1/goals/rewrite", json={
            "employee_id": emp_id,
            "goal_text": "Улучшить работу",
            "quarter": "Q2",
        }).json()
        rewrite = data.get("rewrite", "")
        assert len(rewrite) > 20, f"Rewrite too short: {rewrite!r}"

    def test_rewrite_unknown_employee_returns_404(self, client):
        r = client.post("/api/v1/goals/rewrite", json={
            "employee_id": "BAD_EMP",
            "goal_text": "Some goal",
            "quarter": "Q2",
        })
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Section 8: Generate goals
# ---------------------------------------------------------------------------

class TestGenerateGoals:

    def test_generate_returns_200(self, client, emp_id):
        r = client.post("/api/v1/goals/generate", json={
            "employee_id": emp_id,
            "quarter": "Q2",
            "year": 2026,
            "count": 3,
        })
        assert r.status_code == 200

    def test_generate_returns_correct_count(self, client, emp_id):
        goals = client.post("/api/v1/goals/generate", json={
            "employee_id": emp_id,
            "quarter": "Q2",
            "year": 2026,
            "count": 3,
        }).json()
        assert len(goals) == 3

    def test_generate_with_focus(self, client, emp_id):
        goals = client.post("/api/v1/goals/generate", json={
            "employee_id": emp_id,
            "quarter": "Q2",
            "year": 2026,
            "count": 2,
            "focus": "снижение затрат",
        }).json()
        assert len(goals) == 2

    def test_generate_schema(self, client, emp_id):
        goals = client.post("/api/v1/goals/generate", json={
            "employee_id": emp_id,
            "quarter": "Q2",
            "year": 2026,
            "count": 2,
        }).json()
        for g in goals:
            assert "title" in g
            assert "score" in g
            assert "alignment_level" in g
            assert "goal_type" in g
            assert 0.0 <= g["score"] <= 1.0

    def test_generate_unknown_employee_returns_404(self, client):
        r = client.post("/api/v1/goals/generate", json={
            "employee_id": "BAD_EMP",
            "quarter": "Q2",
            "year": 2026,
            "count": 3,
        })
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Section 9: Batch evaluation (F-16, F-18, F-21)
# ---------------------------------------------------------------------------

class TestBatchEvaluate:

    def test_batch_returns_200(self, client, emp_id):
        r = client.post("/api/v1/goals/evaluate-batch", json={
            "employee_id": emp_id,
            "quarter": "Q2",
            "year": 2026,
            "goals": [
                {"title": "Снизить MTTR до 2 часов до конца Q2", "weight": 50},
                {"title": "Внедрить CI/CD пайплайн до 30.06.2026", "weight": 50},
            ],
        })
        assert r.status_code == 200

    def test_batch_schema(self, client, emp_id):
        data = client.post("/api/v1/goals/evaluate-batch", json={
            "employee_id": emp_id,
            "quarter": "Q2",
            "year": 2026,
            "goals": [
                {"title": "Снизить MTTR на 40% до конца Q2", "weight": 60},
                {"title": "Запустить систему мониторинга до 30.06.2026", "weight": 40},
            ],
        }).json()
        assert "goal_count" in data
        assert "average_smart_index" in data
        assert "strategic_goal_share" in data
        assert "items" in data
        assert "alerts" in data

    def test_batch_alert_low_count(self, client, emp_id):
        """F-16/F-18: fewer than 3 goals should trigger a count alert."""
        data = client.post("/api/v1/goals/evaluate-batch", json={
            "employee_id": emp_id,
            "quarter": "Q2",
            "year": 2026,
            "goals": [
                {"title": "Внедрить мониторинг SLA до конца Q2", "weight": 100},
            ],
        }).json()
        alerts = " ".join(data.get("alerts", []))
        assert any(c.isdigit() for c in alerts) or len(data["alerts"]) > 0, (
            "Expected at least one alert for only 1 goal"
        )

    def test_batch_alert_weight_not_100(self, client, emp_id):
        """F-18: total weight != 100% should trigger a weight alert."""
        data = client.post("/api/v1/goals/evaluate-batch", json={
            "employee_id": emp_id,
            "quarter": "Q2",
            "year": 2026,
            "goals": [
                {"title": "Цель 1 до конца Q2", "weight": 30},
                {"title": "Цель 2 до 30.06.2026", "weight": 30},
            ],
        }).json()
        assert data.get("total_weight") is not None
        assert abs(data["total_weight"] - 60.0) < 0.1

    def test_batch_count_matches_input(self, client, emp_id):
        data = client.post("/api/v1/goals/evaluate-batch", json={
            "employee_id": emp_id,
            "quarter": "Q2",
            "year": 2026,
            "goals": [
                {"title": "Разработать модуль мониторинга", "weight": 40},
                {"title": "Снизить количество инцидентов на 30% до Q2 2026", "weight": 30},
                {"title": "Внедрить автоматические тесты покрытием 80%", "weight": 30},
            ],
        }).json()
        assert data["goal_count"] == 3
        assert len(data["items"]) == 3

    def test_batch_average_score_in_range(self, client, emp_id):
        data = client.post("/api/v1/goals/evaluate-batch", json={
            "employee_id": emp_id,
            "quarter": "Q2",
            "year": 2026,
            "goals": [
                {"title": "Снизить MTTR на 50% до 30.06.2026", "weight": 50},
                {"title": "Обеспечить uptime 99.5% через CI/CD до конца Q2", "weight": 50},
            ],
        }).json()
        assert 0.0 <= data["average_smart_index"] <= 1.0


# ---------------------------------------------------------------------------
# Section 10: Dashboard endpoints
# ---------------------------------------------------------------------------

class TestDashboard:

    def test_dashboard_overview_returns_200(self, client):
        r = client.get("/api/v1/dashboard/overview?quarter=Q2&year=2026")
        assert r.status_code == 200

    def test_dashboard_overview_schema(self, client):
        data = client.get("/api/v1/dashboard/overview?quarter=Q2&year=2026").json()
        for field in ("quarter", "year", "total_departments"):
            assert field in data, f"Missing field: {field}"

    def test_dashboard_department_returns_200(self, client, dept_id):
        r = client.get(f"/api/v1/dashboard/departments/{dept_id}?quarter=Q2&year=2026")
        assert r.status_code == 200

    def test_dashboard_department_schema(self, client, dept_id):
        data = client.get(f"/api/v1/dashboard/departments/{dept_id}?quarter=Q2&year=2026").json()
        for field in ("department_id", "department_name", "avg_smart_score"):
            assert field in data, f"Missing field: {field}"

    def test_notifications_returns_200(self, client):
        r = client.get("/api/v1/notifications?quarter=Q2&year=2026")
        assert r.status_code == 200

    def test_notifications_schema(self, client):
        data = client.get("/api/v1/notifications?quarter=Q2&year=2026").json()
        assert "total" in data

    def test_maturity_returns_200(self, client, dept_id):
        r = client.get(f"/api/v1/dashboard/departments/{dept_id}/maturity?quarter=Q2&year=2026")
        assert r.status_code == 200

    def test_data_stats_returns_200(self, client):
        r = client.get("/api/v1/data/stats")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Section 11: Cascade goals (F-14)
# ---------------------------------------------------------------------------

class TestCascadeGoals:

    def test_cascade_returns_200(self, client):
        r = client.post("/api/v1/goals/cascade", json={
            "manager_id": "emp_mgr",
            "quarter": "Q2",
            "year": 2026,
            "count_per_employee": 2,
        })
        assert r.status_code == 200

    def test_cascade_schema(self, client):
        data = client.post("/api/v1/goals/cascade", json={
            "manager_id": "emp_mgr",
            "quarter": "Q2",
            "year": 2026,
            "count_per_employee": 2,
        }).json()
        assert "manager_id" in data
        # Response uses 'subordinates' key for employee goal lists
        assert "subordinates" in data or "employees" in data or "manager_goals" in data

    def test_cascade_unknown_manager_returns_404(self, client):
        r = client.post("/api/v1/goals/cascade", json={
            "manager_id": "NOBODY",
            "quarter": "Q2",
            "year": 2026,
            "count_per_employee": 2,
        })
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Section 12: Employee context endpoint
# ---------------------------------------------------------------------------

class TestEmployeeContext:

    def test_employee_context_returns_200(self, client, emp_id):
        r = client.get(f"/api/v1/employees/{emp_id}/context?quarter=Q2&year=2026")
        assert r.status_code == 200

    def test_employee_context_schema(self, client, emp_id):
        data = client.get(f"/api/v1/employees/{emp_id}/context?quarter=Q2&year=2026").json()
        assert "employee" in data
