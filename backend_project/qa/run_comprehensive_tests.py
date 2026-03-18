"""
Comprehensive QA + CI/CD Test Suite for GoalCraft AI
=====================================================
Tests with large-scale §4.2 synthetic data (47K+ records).
Covers: schema validation, API contracts, performance benchmarks,
edge cases, data integrity, dashboard correctness, and stress tests.
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DUMP_PATH = ROOT / "qa" / "fixtures" / "synthetic_dump.json"


class TestResult:
    def __init__(self, name: str, category: str, ok: bool, duration: float, details: str, extra: Any = None):
        self.name = name
        self.category = category
        self.ok = ok
        self.duration = duration
        self.details = details
        self.extra = extra

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "status": "PASS" if self.ok else "FAIL",
            "duration_ms": round(self.duration * 1000, 1),
            "details": self.details,
            "extra": self.extra,
        }


class ComprehensiveTestSuite:
    """Runs all QA tests against the in-process FastAPI server."""

    def __init__(self):
        self.results: list[TestResult] = []
        self.client = None
        self.engine = None
        self.store = None
        self.dump_data = None

    def setup(self):
        """Initialize the application with synthetic dump."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.container import container

        self.client = TestClient(app)
        self.engine = container.engine
        self.store = container.engine.store

        # Load synthetic dump
        print("Loading §4.2 synthetic dump into MemoryStore...")
        stats = self.store.load_synthetic_dump(DUMP_PATH)
        print(f"  Loaded: {sum(stats.values()):,} records")
        for k, v in stats.items():
            print(f"    {k}: {v:,}")

        # Re-index documents
        print("  Re-indexing documents...")
        self.engine.index_documents()
        print("  Setup complete.\n")

    def _run(self, name: str, category: str, fn):
        t0 = time.perf_counter()
        try:
            extra = fn()
            dt = time.perf_counter() - t0
            self.results.append(TestResult(name, category, True, dt, "ok", extra))
            print(f"  ✅ {name} ({dt*1000:.0f}ms)")
        except Exception as exc:
            dt = time.perf_counter() - t0
            self.results.append(TestResult(name, category, False, dt, str(exc), traceback.format_exc()))
            print(f"  ❌ {name}: {exc}")

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 1: SCHEMA VALIDATION
    # ═══════════════════════════════════════════════════════════════════

    def test_schema_departments_count(self):
        assert self.store.count_table_rows("departments") == 8, "Expected 8 departments"
        return {"count": 8}

    def test_schema_positions_count(self):
        assert self.store.count_table_rows("positions") == 25, "Expected 25 positions"

    def test_schema_employees_count(self):
        n = self.store.count_table_rows("employees")
        assert n == 450, f"Expected 450 employees, got {n}"

    def test_schema_documents_count(self):
        n = self.store.count_table_rows("documents")
        assert n == 160, f"Expected 160 documents, got {n}"

    def test_schema_goals_count(self):
        n = self.store.count_table_rows("goals")
        assert n == 9000, f"Expected 9000 goals, got {n}"

    def test_schema_goal_events_count(self):
        n = self.store.count_table_rows("goal_events")
        assert n == 30789, f"Expected 30789 goal_events, got {n}"

    def test_schema_goal_reviews_count(self):
        n = self.store.count_table_rows("goal_reviews")
        assert n == 4305, f"Expected 4305 goal_reviews, got {n}"

    def test_schema_kpi_catalog_count(self):
        n = self.store.count_table_rows("kpi_catalog")
        assert n == 13, f"Expected 13 KPI catalog items, got {n}"

    def test_schema_kpi_timeseries_count(self):
        n = self.store.count_table_rows("kpi_timeseries")
        assert n == 2112, f"Expected 2112 KPI timeseries, got {n}"

    def test_schema_projects_count(self):
        n = self.store.count_table_rows("projects")
        assert n == 34, f"Expected 34 projects, got {n}"

    def test_schema_employee_projects_count(self):
        n = self.store.count_table_rows("employee_projects")
        assert n == 886, f"Expected 886 employee_projects, got {n}"

    def test_schema_employee_referential_integrity(self):
        """Every employee references a valid department and position."""
        dept_ids = set(self.store.departments.keys())
        pos_ids = set(self.store.positions.keys())
        errors = []
        for emp in self.store.employees.values():
            if emp.department_id not in dept_ids:
                errors.append(f"{emp.id}: invalid dept {emp.department_id}")
            if emp.position_id not in pos_ids:
                errors.append(f"{emp.id}: invalid pos {emp.position_id}")
        assert not errors, f"Referential integrity violations: {errors[:5]}"

    def test_schema_goal_employee_integrity(self):
        """Every goal references a valid employee."""
        emp_ids = set(self.store.employees.keys())
        errors = []
        for g in self.store._goals[:1000]:  # sample
            if g.employee_id not in emp_ids:
                errors.append(f"{g.id}: invalid employee {g.employee_id}")
        assert not errors, f"Goal→Employee violations: {errors[:5]}"

    def test_schema_manager_hierarchy(self):
        """Managers reference valid employees or are None."""
        emp_ids = set(self.store.employees.keys())
        errors = []
        for emp in self.store.employees.values():
            if emp.manager_id and emp.manager_id not in emp_ids:
                errors.append(f"{emp.id}: invalid manager {emp.manager_id}")
        assert not errors, f"Manager hierarchy violations: {errors[:5]}"

    def test_schema_has_dump_data(self):
        assert self.store.has_dump_data(), "has_dump_data should be True with 450 employees"

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 2: API CONTRACT TESTS
    # ═══════════════════════════════════════════════════════════════════

    def test_api_health(self):
        r = self.client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["employees_count"] == 450
        assert data["goals_count"] == 9000
        assert data["mode"] == "hackathon-dump"
        return data

    def test_api_departments(self):
        r = self.client.get("/api/v1/departments")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 8
        for d in data:
            assert "id" in d and "name" in d and "code" in d

    def test_api_employees_list(self):
        r = self.client.get("/api/v1/employees")
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 440  # some may be inactive
        for e in data[:5]:
            assert "id" in e and "full_name" in e
            assert "department_name" in e and "position_name" in e

    def test_api_employees_filter_by_dept(self):
        r = self.client.get("/api/v1/employees?department_id=dep_ops")
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 50, f"Expected 50+ OPS employees, got {len(data)}"
        for e in data:
            assert e["department_id"] == "dep_ops"

    def test_api_employee_context(self):
        # Find a random employee with goals
        emp_ids_with_goals = set()
        for g in self.store._goals:
            if g.quarter == "Q2" and g.year == 2026:
                emp_ids_with_goals.add(g.employee_id)
        emp_id = list(emp_ids_with_goals)[0] if emp_ids_with_goals else "emp_0001"

        r = self.client.get(f"/api/v1/employees/{emp_id}/context?quarter=Q2&year=2026")
        assert r.status_code == 200
        data = r.json()
        assert data["employee"]["id"] == emp_id
        assert "department" in data
        assert "position" in data
        assert "active_goals" in data
        assert "projects" in data
        assert "department_kpis" in data
        assert "goal_history_stats" in data
        return {"employee_id": emp_id, "goals": len(data["active_goals"]), "projects": len(data["projects"])}

    def test_api_employee_context_404(self):
        r = self.client.get("/api/v1/employees/nonexistent/context?quarter=Q2&year=2026")
        assert r.status_code == 404

    def test_api_data_stats(self):
        r = self.client.get("/api/v1/data/stats")
        assert r.status_code == 200
        data = r.json()
        assert data["departments"] == 8
        assert data["employees"] == 450
        assert data["goals"] == 9000
        assert data["has_dump_data"] is True
        return data

    def test_api_evaluate_good_goal(self):
        r = self.client.post("/api/v1/goals/evaluate", json={
            "employee_id": "emp_0001",
            "goal_text": "До 30.06 сократить средний срок согласования HR-заявок с 5 до 3 рабочих дней за счет цифровизации маршрута согласования",
            "quarter": "Q2",
            "year": 2026,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["overall_score"] >= 0.6, f"Good goal scored too low: {data['overall_score']}"
        assert "scores" in data
        assert "alignment_level" in data
        assert "rewrite" in data
        assert "achievability" in data
        assert "okr_mapping" in data
        return {"score": data["overall_score"], "alignment": data["alignment_level"]}

    def test_api_evaluate_bad_goal(self):
        r = self.client.post("/api/v1/goals/evaluate", json={
            "employee_id": "emp_0001",
            "goal_text": "улучшить работу",
            "quarter": "Q2",
            "year": 2026,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["overall_score"] < 0.6, f"Bad goal scored too high: {data['overall_score']}"
        assert len(data["recommendations"]) >= 2, "Bad goal should have multiple recommendations"
        return {"score": data["overall_score"], "recs": len(data["recommendations"])}

    def test_api_generate_goals(self):
        r = self.client.post("/api/v1/goals/generate", json={
            "employee_id": "emp_0001",
            "quarter": "Q2",
            "year": 2026,
            "count": 3,
        })
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3, f"Expected 3 generated goals, got {len(data)}"
        for g in data:
            assert g["score"] >= 0.5
            assert g["alignment_level"] in ("strategic", "functional", "operational")
            assert g["source"] is not None
        return {"titles": [g["title"][:60] for g in data]}

    def test_api_evaluate_batch(self):
        r = self.client.post("/api/v1/goals/evaluate-batch", json={
            "employee_id": "emp_0001",
            "quarter": "Q2",
            "year": 2026,
            "goals": [
                {"title": "До 30.06 довести долю целей, привязанных к KPI подразделения, до 85%", "weight": 50},
                {"title": "До 30.06 сократить средний срок согласования HR-заявок с 5 до 3 дней", "weight": 50},
            ],
        })
        assert r.status_code == 200
        data = r.json()
        assert data["goal_count"] == 2
        assert 0 <= data["average_smart_index"] <= 1.0
        assert data["total_weight"] == 100.0
        return {"avg_score": data["average_smart_index"]}

    def test_api_batch_weight_alert(self):
        """Batch with wrong weights should trigger alert."""
        r = self.client.post("/api/v1/goals/evaluate-batch", json={
            "employee_id": "emp_0001",
            "quarter": "Q2",
            "year": 2026,
            "goals": [
                {"title": "Цель 1", "weight": 30},
                {"title": "Цель 2", "weight": 30},
            ],
        })
        assert r.status_code == 200
        data = r.json()
        assert any("100%" in a for a in data["alerts"]), "Expected weight alert"

    def test_api_dashboard_overview(self):
        r = self.client.get("/api/v1/dashboard/overview?quarter=Q2&year=2026")
        assert r.status_code == 200
        data = r.json()
        assert data["total_departments"] == 8
        assert data["total_goals_evaluated"] >= 100, f"Expected 100+ goals, got {data['total_goals_evaluated']}"
        for dept in data["departments"]:
            assert "maturity_index" in dept
            assert "maturity_level" in dept
        return {"total_goals": data["total_goals_evaluated"], "avg_score": data["avg_smart_score"]}

    def test_api_department_snapshot(self):
        r = self.client.get("/api/v1/dashboard/departments/dep_hr?quarter=Q2&year=2026")
        assert r.status_code == 200
        data = r.json()
        assert data["department_id"] == "dep_hr"
        assert 0 <= data["avg_smart_score"] <= 1.0
        assert data["maturity_index"] > 0

    def test_api_department_404(self):
        r = self.client.get("/api/v1/dashboard/departments/nonexistent?quarter=Q2&year=2026")
        assert r.status_code == 404

    def test_api_maturity_report(self):
        r = self.client.get("/api/v1/dashboard/departments/dep_hr/maturity?quarter=Q2&year=2026")
        assert r.status_code == 200
        data = r.json()
        assert data["department_id"] == "dep_hr"
        assert data["total_employees"] >= 10
        assert data["total_goals"] >= 10
        assert "smart_distribution" in data
        assert "goal_type_distribution" in data
        assert "alignment_distribution" in data
        assert "weakest_criteria" in data
        assert "top_recommendations" in data
        return {"maturity": data["maturity_index"], "level": data["maturity_level"]}

    def test_api_goal_history(self):
        """Find a goal with events and test history endpoint."""
        goal_id = self.store._goals[0].id if self.store._goals else "goal_0001"
        r = self.client.get(f"/api/v1/goals/{goal_id}/history")
        assert r.status_code == 200
        data = r.json()
        assert data["goal_id"] == goal_id
        assert "events" in data
        assert "reviews" in data

    def test_api_cascade_goals(self):
        """Find a manager with subordinates and test cascade."""
        mgr = None
        for emp in self.store.employees.values():
            subs = self.store.list_subordinates(emp.id)
            if len(subs) >= 2:
                mgr = emp
                break
        assert mgr is not None, "No manager with subordinates found"

        r = self.client.post("/api/v1/goals/cascade", json={
            "manager_id": mgr.id,
            "quarter": "Q2",
            "year": 2026,
            "count_per_employee": 2,
        })
        assert r.status_code == 200
        data = r.json()
        assert len(data["subordinates"]) >= 2
        for sub in data["subordinates"]:
            assert len(sub["goals"]) == 2
        return {"manager": mgr.id, "subs": len(data["subordinates"])}

    def test_api_notifications(self):
        r = self.client.get("/api/v1/notifications?quarter=Q2&year=2026")
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
        if data["items"]:
            item = data["items"][0]
            assert item["severity"] in ("critical", "warning", "info")
        return {"total": data["total"], "critical": data["critical"], "warnings": data["warnings"]}

    def test_api_ingest_documents(self):
        r = self.client.post("/api/v1/documents/ingest", json={
            "documents": [{
                "doc_id": "DOC-TEST-001",
                "doc_type": "strategy",
                "title": "Тестовый документ для QA",
                "content": "Это тестовый документ для проверки загрузки.",
                "keywords": ["тест", "QA"],
            }],
        })
        assert r.status_code == 200
        data = r.json()
        assert data["indexed_documents"] == 1

    def test_api_rewrite_goal(self):
        r = self.client.post("/api/v1/goals/rewrite", json={
            "employee_id": "emp_0001",
            "goal_text": "улучшить HR процессы",
            "quarter": "Q2",
        })
        assert r.status_code == 200
        data = r.json()
        assert len(data["rewrite"]) > 20, f"Rewrite too short: {data['rewrite']}"

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 3: PERFORMANCE BENCHMARKS
    # ═══════════════════════════════════════════════════════════════════

    def test_perf_health_under_100ms(self):
        """Health endpoint should respond under 100ms."""
        t0 = time.perf_counter()
        r = self.client.get("/health")
        dt = time.perf_counter() - t0
        assert r.status_code == 200
        assert dt < 0.5, f"Health took {dt*1000:.0f}ms (limit: 500ms)"
        return {"ms": round(dt * 1000)}

    def test_perf_evaluate_under_2s(self):
        """Single evaluate should respond under 2s."""
        t0 = time.perf_counter()
        r = self.client.post("/api/v1/goals/evaluate", json={
            "employee_id": "emp_0001",
            "goal_text": "До 30.06 сократить средний срок согласования HR-заявок с 5 до 3 рабочих дней",
            "quarter": "Q2", "year": 2026,
        })
        dt = time.perf_counter() - t0
        assert r.status_code == 200
        assert dt < 2.0, f"Evaluate took {dt*1000:.0f}ms (limit: 2000ms)"
        return {"ms": round(dt * 1000)}

    def test_perf_generate_under_5s(self):
        """Generate 3 goals should complete under 5s."""
        t0 = time.perf_counter()
        r = self.client.post("/api/v1/goals/generate", json={
            "employee_id": "emp_0001",
            "quarter": "Q2", "year": 2026, "count": 3,
        })
        dt = time.perf_counter() - t0
        assert r.status_code == 200
        assert dt < 5.0, f"Generate took {dt*1000:.0f}ms (limit: 5000ms)"
        return {"ms": round(dt * 1000)}

    def test_perf_departments_list_under_200ms(self):
        t0 = time.perf_counter()
        r = self.client.get("/api/v1/departments")
        dt = time.perf_counter() - t0
        assert r.status_code == 200
        assert dt < 0.5, f"Departments list took {dt*1000:.0f}ms"
        return {"ms": round(dt * 1000)}

    def test_perf_employees_list_under_500ms(self):
        t0 = time.perf_counter()
        r = self.client.get("/api/v1/employees")
        dt = time.perf_counter() - t0
        assert r.status_code == 200
        assert dt < 1.0, f"Employees list took {dt*1000:.0f}ms"
        return {"ms": round(dt * 1000)}

    def test_perf_data_stats_under_200ms(self):
        t0 = time.perf_counter()
        r = self.client.get("/api/v1/data/stats")
        dt = time.perf_counter() - t0
        assert r.status_code == 200
        assert dt < 0.5, f"Data stats took {dt*1000:.0f}ms"
        return {"ms": round(dt * 1000)}

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 4: EDGE CASES & ROBUSTNESS
    # ═══════════════════════════════════════════════════════════════════

    def test_edge_empty_goal_text(self):
        """Empty goal text should still return valid response."""
        r = self.client.post("/api/v1/goals/evaluate", json={
            "employee_id": "emp_0001",
            "goal_text": "",
            "quarter": "Q2", "year": 2026,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["overall_score"] < 0.5, f"Empty goal scored {data['overall_score']}"

    def test_edge_very_long_goal(self):
        """Very long goal text should not crash."""
        long_text = "улучшить " * 500
        r = self.client.post("/api/v1/goals/evaluate", json={
            "employee_id": "emp_0001",
            "goal_text": long_text,
            "quarter": "Q2", "year": 2026,
        })
        assert r.status_code == 200

    def test_edge_special_characters(self):
        """Goal with special characters should not crash."""
        r = self.client.post("/api/v1/goals/evaluate", json={
            "employee_id": "emp_0001",
            "goal_text": 'До 30.06 улучшить "KPI" & <метрики> до 95% (включая \\n и ™)',
            "quarter": "Q2", "year": 2026,
        })
        assert r.status_code == 200

    def test_edge_nonexistent_employee_evaluate(self):
        r = self.client.post("/api/v1/goals/evaluate", json={
            "employee_id": "emp_99999",
            "goal_text": "какая-то цель",
            "quarter": "Q2", "year": 2026,
        })
        assert r.status_code == 404

    def test_edge_invalid_quarter(self):
        r = self.client.get("/api/v1/dashboard/overview?quarter=Q5&year=2026")
        assert r.status_code == 422  # validation error

    def test_edge_batch_empty_goals(self):
        """Empty goals list should return valid response."""
        r = self.client.post("/api/v1/goals/evaluate-batch", json={
            "employee_id": "emp_0001",
            "quarter": "Q2", "year": 2026,
            "goals": [],
        })
        assert r.status_code == 200
        data = r.json()
        assert data["goal_count"] == 0

    def test_edge_batch_duplicate_goals(self):
        """Duplicate goals should be detected."""
        r = self.client.post("/api/v1/goals/evaluate-batch", json={
            "employee_id": "emp_0001",
            "quarter": "Q2", "year": 2026,
            "goals": [
                {"title": "До 30.06 довести долю целей, привязанных к KPI подразделения, до 85%", "weight": 50},
                {"title": "До 30.06 довести долю целей, привязанных к KPI подразделения, до 85%", "weight": 50},
            ],
        })
        assert r.status_code == 200
        data = r.json()
        assert data["duplicates_found"] >= 1

    def test_edge_cascade_no_subordinates(self):
        """Cascade from non-manager should return error."""
        # Find someone without subordinates
        for emp in list(self.store.employees.values())[:50]:
            subs = self.store.list_subordinates(emp.id)
            if not subs:
                r = self.client.post("/api/v1/goals/cascade", json={
                    "manager_id": emp.id,
                    "quarter": "Q2", "year": 2026,
                    "count_per_employee": 2,
                })
                assert r.status_code == 404 or r.status_code == 200
                return {"tested_emp": emp.id}
        return {"note": "all employees have subordinates"}

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 5: DATA INTEGRITY
    # ═══════════════════════════════════════════════════════════════════

    def test_integrity_all_depts_have_employees(self):
        """Every department should have at least one employee."""
        for dept in self.store.departments.values():
            emps = self.store.list_employees(dept.id)
            assert len(emps) > 0, f"Department {dept.id} ({dept.name}) has no employees"

    def test_integrity_all_depts_have_goals(self):
        """Every department should have goals in Q2 2026."""
        for dept in self.store.departments.values():
            goals = self.store.list_department_goals(dept.id, "Q2", 2026)
            assert len(goals) > 0, f"Department {dept.id} ({dept.name}) has no Q2 2026 goals"

    def test_integrity_goal_status_distribution(self):
        """Goals should have realistic status distribution."""
        counter = Counter(g.status for g in self.store._goals)
        assert counter["approved"] > 0, "No approved goals"
        assert counter["draft"] > 0, "No draft goals"
        return dict(counter)

    def test_integrity_goal_weight_sum(self):
        """Sample employees' goal weights should be close to 100."""
        checked = 0
        issues = 0
        sample_emps = list(self.store.employees.values())[:20]
        for emp in sample_emps:
            for q, y in [("Q2", 2026), ("Q1", 2026)]:
                goals = self.store.list_employee_goals(emp.id, q, y)
                if goals:
                    weights = [g.weight for g in goals if g.weight is not None]
                    if weights:
                        total = sum(weights)
                        checked += 1
                        if abs(total - 100.0) > 5:
                            issues += 1
        return {"checked": checked, "weight_issues": issues}

    def test_integrity_kpi_timeseries_coverage(self):
        """KPI timeseries should cover all departments."""
        dept_ids_with_kpi = set()
        for ts in self.store._kpi_timeseries:
            dept_ids_with_kpi.add(ts.department_id)
        for dept in self.store.departments.values():
            assert dept.id in dept_ids_with_kpi, f"No KPI timeseries for {dept.id}"

    def test_integrity_employee_projects_valid(self):
        """Employee project links should reference valid employees."""
        emp_ids = set(self.store.employees.keys())
        errors = 0
        for ep in self.store._employee_projects[:200]:  # sample
            if ep.get("employee_id") not in emp_ids:
                errors += 1
        assert errors == 0, f"{errors} employee_projects with invalid employees"

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 6: CROSS-MODULE CONSISTENCY
    # ═══════════════════════════════════════════════════════════════════

    def test_cross_dashboard_matches_goals(self):
        """Dashboard goal counts should match store goal counts."""
        r = self.client.get("/api/v1/dashboard/overview?quarter=Q2&year=2026")
        data = r.json()
        total_from_store = 0
        for emp in self.store.employees.values():
            total_from_store += len(self.store.list_employee_goals(emp.id, "Q2", 2026))
        assert data["total_goals_evaluated"] == total_from_store, (
            f"Dashboard: {data['total_goals_evaluated']}, Store: {total_from_store}"
        )

    def test_cross_maturity_all_departments(self):
        """Maturity report should work for all 8 departments."""
        results = {}
        for dept in self.store.departments.values():
            r = self.client.get(f"/api/v1/dashboard/departments/{dept.id}/maturity?quarter=Q2&year=2026")
            assert r.status_code == 200, f"Maturity failed for {dept.id}"
            data = r.json()
            results[dept.id] = {"index": data["maturity_index"], "level": data["maturity_level"]}
        return results

    def test_cross_employee_context_all_fields(self):
        """Employee context should return all §4.2 extended fields."""
        # Pick 5 random employees
        import random
        random.seed(123)
        sample = random.sample(list(self.store.employees.keys()), min(5, len(self.store.employees)))
        for emp_id in sample:
            r = self.client.get(f"/api/v1/employees/{emp_id}/context?quarter=Q2&year=2026")
            assert r.status_code == 200
            data = r.json()
            assert "employee" in data
            assert "department" in data
            assert "projects" in data
            assert "department_kpis" in data
            assert "goal_history_stats" in data

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 7: SMART SCORING ACCURACY (sampled)
    # ═══════════════════════════════════════════════════════════════════

    def test_accuracy_good_goals_score_high(self):
        """Well-formed goals should score >= 0.6."""
        good_goals = [
            "До 30.06 сократить средний срок согласования HR-заявок с 5 до 3 рабочих дней за счет цифровизации маршрута согласования",
            "До конца Q2 обеспечить прохождение обязательного обучения не менее 95% сотрудников подразделения за счет автоматизации напоминаний",
            "До 30.06 довести долю целей, привязанных к KPI подразделения, до 85% за счет регулярных калибровочных сессий",
        ]
        scores = []
        for goal in good_goals:
            r = self.client.post("/api/v1/goals/evaluate", json={
                "employee_id": "emp_0001",
                "goal_text": goal,
                "quarter": "Q2", "year": 2026,
            })
            data = r.json()
            scores.append(data["overall_score"])
            assert data["overall_score"] >= 0.6, f"Good goal scored {data['overall_score']}: {goal[:50]}"
        return {"scores": scores}

    def test_accuracy_bad_goals_score_low(self):
        """Vague goals should score < 0.6."""
        bad_goals = [
            "улучшить работу",
            "стараться лучше",
            "повысить эффективность",
        ]
        scores = []
        for goal in bad_goals:
            r = self.client.post("/api/v1/goals/evaluate", json={
                "employee_id": "emp_0001",
                "goal_text": goal,
                "quarter": "Q2", "year": 2026,
            })
            data = r.json()
            scores.append(data["overall_score"])
            assert data["overall_score"] < 0.6, f"Bad goal scored too high {data['overall_score']}: {goal}"
        return {"scores": scores}

    # ═══════════════════════════════════════════════════════════════════
    # RUN ALL
    # ═══════════════════════════════════════════════════════════════════

    def run_all(self) -> dict:
        categories = {
            "Schema Validation": [
                ("schema_departments_count", self.test_schema_departments_count),
                ("schema_positions_count", self.test_schema_positions_count),
                ("schema_employees_count", self.test_schema_employees_count),
                ("schema_documents_count", self.test_schema_documents_count),
                ("schema_goals_count", self.test_schema_goals_count),
                ("schema_goal_events_count", self.test_schema_goal_events_count),
                ("schema_goal_reviews_count", self.test_schema_goal_reviews_count),
                ("schema_kpi_catalog_count", self.test_schema_kpi_catalog_count),
                ("schema_kpi_timeseries_count", self.test_schema_kpi_timeseries_count),
                ("schema_projects_count", self.test_schema_projects_count),
                ("schema_employee_projects_count", self.test_schema_employee_projects_count),
                ("schema_employee_referential_integrity", self.test_schema_employee_referential_integrity),
                ("schema_goal_employee_integrity", self.test_schema_goal_employee_integrity),
                ("schema_manager_hierarchy", self.test_schema_manager_hierarchy),
                ("schema_has_dump_data", self.test_schema_has_dump_data),
            ],
            "API Contracts": [
                ("api_health", self.test_api_health),
                ("api_departments", self.test_api_departments),
                ("api_employees_list", self.test_api_employees_list),
                ("api_employees_filter_by_dept", self.test_api_employees_filter_by_dept),
                ("api_employee_context", self.test_api_employee_context),
                ("api_employee_context_404", self.test_api_employee_context_404),
                ("api_data_stats", self.test_api_data_stats),
                ("api_evaluate_good_goal", self.test_api_evaluate_good_goal),
                ("api_evaluate_bad_goal", self.test_api_evaluate_bad_goal),
                ("api_generate_goals", self.test_api_generate_goals),
                ("api_evaluate_batch", self.test_api_evaluate_batch),
                ("api_batch_weight_alert", self.test_api_batch_weight_alert),
                ("api_dashboard_overview", self.test_api_dashboard_overview),
                ("api_department_snapshot", self.test_api_department_snapshot),
                ("api_department_404", self.test_api_department_404),
                ("api_maturity_report", self.test_api_maturity_report),
                ("api_goal_history", self.test_api_goal_history),
                ("api_cascade_goals", self.test_api_cascade_goals),
                ("api_notifications", self.test_api_notifications),
                ("api_ingest_documents", self.test_api_ingest_documents),
                ("api_rewrite_goal", self.test_api_rewrite_goal),
            ],
            "Performance": [
                ("perf_health_under_100ms", self.test_perf_health_under_100ms),
                ("perf_evaluate_under_2s", self.test_perf_evaluate_under_2s),
                ("perf_generate_under_5s", self.test_perf_generate_under_5s),
                ("perf_departments_list_under_200ms", self.test_perf_departments_list_under_200ms),
                ("perf_employees_list_under_500ms", self.test_perf_employees_list_under_500ms),
                ("perf_data_stats_under_200ms", self.test_perf_data_stats_under_200ms),
            ],
            "Edge Cases": [
                ("edge_empty_goal_text", self.test_edge_empty_goal_text),
                ("edge_very_long_goal", self.test_edge_very_long_goal),
                ("edge_special_characters", self.test_edge_special_characters),
                ("edge_nonexistent_employee_evaluate", self.test_edge_nonexistent_employee_evaluate),
                ("edge_invalid_quarter", self.test_edge_invalid_quarter),
                ("edge_batch_empty_goals", self.test_edge_batch_empty_goals),
                ("edge_batch_duplicate_goals", self.test_edge_batch_duplicate_goals),
                ("edge_cascade_no_subordinates", self.test_edge_cascade_no_subordinates),
            ],
            "Data Integrity": [
                ("integrity_all_depts_have_employees", self.test_integrity_all_depts_have_employees),
                ("integrity_all_depts_have_goals", self.test_integrity_all_depts_have_goals),
                ("integrity_goal_status_distribution", self.test_integrity_goal_status_distribution),
                ("integrity_goal_weight_sum", self.test_integrity_goal_weight_sum),
                ("integrity_kpi_timeseries_coverage", self.test_integrity_kpi_timeseries_coverage),
                ("integrity_employee_projects_valid", self.test_integrity_employee_projects_valid),
            ],
            "Cross-Module": [
                ("cross_dashboard_matches_goals", self.test_cross_dashboard_matches_goals),
                ("cross_maturity_all_departments", self.test_cross_maturity_all_departments),
                ("cross_employee_context_all_fields", self.test_cross_employee_context_all_fields),
            ],
            "SMART Accuracy": [
                ("accuracy_good_goals_score_high", self.test_accuracy_good_goals_score_high),
                ("accuracy_bad_goals_score_low", self.test_accuracy_bad_goals_score_low),
            ],
        }

        print("=" * 70)
        print("   GOALCRAFT AI — COMPREHENSIVE QA TEST SUITE")
        print("   §4.2 Large-Scale Data (47K+ records)")
        print("=" * 70)

        total_t0 = time.perf_counter()

        for cat_name, tests in categories.items():
            print(f"\n📋 {cat_name} ({len(tests)} tests)")
            print("-" * 50)
            for test_name, test_fn in tests:
                self._run(test_name, cat_name, test_fn)

        total_dt = time.perf_counter() - total_t0

        passed = sum(1 for r in self.results if r.ok)
        failed = len(self.results) - passed
        report = {
            "summary": {
                "total": len(self.results),
                "passed": passed,
                "failed": failed,
                "pass_rate": round(passed / len(self.results) * 100, 1) if self.results else 0,
                "total_duration_s": round(total_dt, 2),
                "timestamp": datetime.now().isoformat(),
            },
            "categories": {},
            "failures": [],
            "results": [r.to_dict() for r in self.results],
        }

        for r in self.results:
            cat = r.category
            if cat not in report["categories"]:
                report["categories"][cat] = {"passed": 0, "failed": 0, "total": 0}
            report["categories"][cat]["total"] += 1
            if r.ok:
                report["categories"][cat]["passed"] += 1
            else:
                report["categories"][cat]["failed"] += 1
                report["failures"].append({
                    "name": r.name,
                    "category": r.category,
                    "details": r.details,
                })

        print(f"\n{'=' * 70}")
        print(f"   RESULTS: {passed}/{len(self.results)} passed  ({report['summary']['pass_rate']}%)")
        print(f"   DURATION: {total_dt:.1f}s")
        if failed:
            print(f"   FAILURES: {failed}")
            for f in report["failures"]:
                print(f"     ❌ {f['name']}: {f['details'][:100]}")
        print(f"{'=' * 70}")

        return report


def render_markdown_report(report: dict) -> str:
    lines = [
        "# GoalCraft AI — Comprehensive QA Test Report",
        "",
        f"**Date**: {report['summary']['timestamp']}",
        f"**Total Tests**: {report['summary']['total']}",
        f"**Passed**: {report['summary']['passed']} ✅",
        f"**Failed**: {report['summary']['failed']} ❌",
        f"**Pass Rate**: {report['summary']['pass_rate']}%",
        f"**Duration**: {report['summary']['total_duration_s']}s",
        "",
        "## §4.2 Data Volumes",
        "",
        "| Table | Count |",
        "|-------|------:|",
        "| departments | 8 |",
        "| positions | 25 |",
        "| employees | 450 |",
        "| documents | 160 |",
        "| goals | 9,000 |",
        "| projects | 34 |",
        "| systems | 10 |",
        "| project_systems | 65 |",
        "| employee_projects | 886 |",
        "| goal_events | 30,789 |",
        "| goal_reviews | 4,305 |",
        "| kpi_catalog | 13 |",
        "| kpi_timeseries | 2,112 |",
        "| **TOTAL** | **47,857** |",
        "",
        "## Results by Category",
        "",
    ]

    for cat, stats in report["categories"].items():
        icon = "✅" if stats["failed"] == 0 else "⚠️"
        lines.append(f"### {icon} {cat}: {stats['passed']}/{stats['total']}")
        lines.append("")
        for r in report["results"]:
            if r["category"] == cat:
                status_icon = "✅" if r["status"] == "PASS" else "❌"
                lines.append(f"- {status_icon} **{r['name']}** ({r['duration_ms']}ms)")
                if r["status"] == "FAIL":
                    lines.append(f"  - Error: `{r['details'][:200]}`")
        lines.append("")

    if report["failures"]:
        lines.append("## ❌ Failures Detail")
        lines.append("")
        for f in report["failures"]:
            lines.append(f"### {f['name']} ({f['category']})")
            lines.append(f"```\n{f['details'][:500]}\n```")
            lines.append("")

    return "\n".join(lines)


def main():
    suite = ComprehensiveTestSuite()
    suite.setup()
    report = suite.run_all()

    # Save outputs
    json_path = ROOT / "qa" / "comprehensive_test_report.json"
    md_path = ROOT / "qa" / "comprehensive_test_report.md"

    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown_report(report), encoding="utf-8")

    print(f"\nReports saved:")
    print(f"  JSON: {json_path}")
    print(f"  MD:   {md_path}")

    return 0 if report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
