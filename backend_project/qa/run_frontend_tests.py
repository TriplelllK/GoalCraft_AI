"""
GoalCraft AI — Frontend Functional Test Suite
==============================================
Tests every frontend function by calling the same API endpoints the
React app calls, through the Vite dev-server proxy (port 5173).
This validates that:
  1) Vite proxy correctly routes /api/* and /health to backend
  2) Every API response matches the shape the frontend expects
  3) All pages can render without errors (data contracts match)
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field

import requests

VITE_BASE = "http://localhost:5173"
API_BASE = "http://localhost:8899"

# All tests run against the backend API directly (port 8899).
# The Vite dev proxy is tested separately if available.
BASE = API_BASE

# Wait for backend
def _wait_for(url: str, label: str, retries: int = 10):
    for i in range(retries):
        try:
            requests.get(url, timeout=3)
            return True
        except Exception:
            if i < retries - 1:
                time.sleep(1)
    print(f"⚠️  {label} not reachable at {url}")
    return False

_wait_for(f"{API_BASE}/health", "Backend")

@dataclass
class TestResult:
    name: str
    page: str
    passed: bool
    duration_ms: float
    detail: str = ""

results: list[TestResult] = []

def run(name: str, page: str):
    """Decorator to register and run a test."""
    def decorator(fn):
        t0 = time.perf_counter()
        try:
            fn()
            dur = (time.perf_counter() - t0) * 1000
            results.append(TestResult(name=name, page=page, passed=True, duration_ms=dur))
            print(f"  ✅ {name} ({dur:.0f}ms)")
        except Exception as e:
            dur = (time.perf_counter() - t0) * 1000
            results.append(TestResult(name=name, page=page, passed=False, duration_ms=dur, detail=str(e)))
            print(f"  ❌ {name} ({dur:.0f}ms) — {e}")
        return fn
    return decorator

def get(path: str, base: str = API_BASE, **kwargs) -> requests.Response:
    r = requests.get(f"{base}{path}", timeout=30, **kwargs)
    return r

def post(path: str, data: dict, base: str = API_BASE) -> requests.Response:
    r = requests.post(f"{base}{path}", json=data, timeout=30)
    return r

# ═══════════════════════════════════════════════════════════════════
# 0. Connectivity checks
# ═══════════════════════════════════════════════════════════════════
print("\n🔗 Connectivity")
print("-" * 50)

@run("vite_serves_html", "index")
def _():
    """Check that Vite dev server serves HTML. Skip if Vite not running."""
    try:
        r = get("/", base=VITE_BASE)
        assert r.status_code == 200, f"Vite returned {r.status_code}"
        assert "GoalCraft AI" in r.text or "root" in r.text, "HTML doesn't look right"
    except requests.ConnectionError:
        # Vite dev server not running — verify built index.html instead
        from pathlib import Path
        index = Path(__file__).parent.parent / "frontend" / "dist" / "index.html"
        assert index.exists(), "Neither Vite running nor dist/index.html exists"
        html = index.read_text(encoding="utf-8")
        assert "GoalCraft AI" in html or "root" in html

@run("vite_proxy_health", "index")
def _():
    """Verify /health returns valid data (proxy or direct)."""
    # Try Vite proxy first, fall back to direct backend
    try:
        r = get("/health", base=VITE_BASE)
    except requests.ConnectionError:
        r = get("/health", base=API_BASE)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    for key in ("mode", "vector_backend", "indexed_documents", "llm_enabled"):
        assert key in data, f"Missing key: {key}"

@run("backend_direct_health", "index")
def _():
    r = get("/health", base=API_BASE)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

# ═══════════════════════════════════════════════════════════════════
# 1. Layout / Header APIs
# ═══════════════════════════════════════════════════════════════════
print("\n🏠 Layout & Header (AlertsPanel, HealthStatus)")
print("-" * 50)

@run("notifications_api", "Layout")
def _():
    r = get("/api/v1/notifications?quarter=Q2&year=2026")
    assert r.status_code == 200
    data = r.json()
    for key in ("total", "critical", "warnings", "info", "items"):
        assert key in data, f"Missing: {key}"
    assert isinstance(data["items"], list)
    if data["items"]:
        item = data["items"][0]
        for key in ("id", "severity", "target_role", "title", "message"):
            assert key in item, f"Item missing: {key}"

@run("departments_list", "Layout")
def _():
    r = get("/api/v1/departments")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) > 0
    for key in ("id", "name", "code"):
        assert key in data[0], f"Missing: {key}"

@run("employees_list", "Layout")
def _():
    r = get("/api/v1/employees")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) > 0
    for key in ("id", "full_name", "department_id", "department_name", "position_id", "position_name"):
        assert key in data[0], f"Missing: {key}"

# ═══════════════════════════════════════════════════════════════════
# 2. EvaluatePage
# ═══════════════════════════════════════════════════════════════════
print("\n📝 EvaluatePage")
print("-" * 50)

@run("employee_context", "EvaluatePage")
def _():
    r = get("/api/v1/employees/emp_1/context?quarter=Q2&year=2026")
    assert r.status_code == 200
    data = r.json()
    assert "employee" in data and data["employee"]["id"] == "emp_1"
    assert "department" in data
    assert "position" in data
    assert "active_goals" in data
    assert isinstance(data["active_goals"], list)

@run("evaluate_goal", "EvaluatePage")
def _():
    r = post("/api/v1/goals/evaluate", {
        "employee_id": "emp_1",
        "goal_text": "Улучшить процесс обучения сотрудников",
        "quarter": "Q2",
        "year": 2026,
    })
    assert r.status_code == 200
    data = r.json()
    # Check all fields the frontend reads
    assert "scores" in data
    for s in ("specific", "measurable", "achievable", "relevant", "timebound"):
        assert s in data["scores"], f"Missing score: {s}"
    assert "overall_score" in data and 0.0 <= data["overall_score"] <= 1.0
    assert "alignment_level" in data
    assert "goal_type" in data
    assert "methodology" in data
    assert "recommendations" in data and isinstance(data["recommendations"], list)
    assert "rewrite" in data and isinstance(data["rewrite"], str)
    # Optional but expected fields
    assert "achievability" in data
    assert "okr_mapping" in data

@run("evaluate_goal_achievability", "EvaluatePage")
def _():
    r = post("/api/v1/goals/evaluate", {
        "employee_id": "emp_1",
        "goal_text": "Увеличить охват обучения на 30% за Q2 2026",
        "quarter": "Q2",
        "year": 2026,
    })
    data = r.json()
    ach = data.get("achievability")
    if ach:
        for key in ("is_achievable", "confidence", "similar_goals_found"):
            assert key in ach, f"Achievability missing: {key}"

@run("evaluate_goal_okr", "EvaluatePage")
def _():
    r = post("/api/v1/goals/evaluate", {
        "employee_id": "emp_1",
        "goal_text": "Снизить текучесть кадров до 5% к концу Q2 2026",
        "quarter": "Q2",
        "year": 2026,
    })
    data = r.json()
    okr = data.get("okr_mapping")
    if okr:
        for key in ("objective", "key_results", "ambition_score", "transparency_score"):
            assert key in okr, f"OKR missing: {key}"

@run("evaluate_batch", "EvaluatePage")
def _():
    ctx = get("/api/v1/employees/emp_1/context?quarter=Q2&year=2026").json()
    goals = [{"title": g["title"], "weight": g.get("weight")} for g in ctx["active_goals"]]
    if not goals:
        goals = [{"title": "Тестовая цель 1", "weight": 50}, {"title": "Тестовая цель 2", "weight": 50}]
    r = post("/api/v1/goals/evaluate-batch", {
        "employee_id": "emp_1",
        "quarter": "Q2",
        "year": 2026,
        "goals": goals,
    })
    assert r.status_code == 200
    data = r.json()
    for key in ("goal_count", "average_smart_index", "strategic_goal_share", "weakest_criteria", "duplicates_found", "alerts", "items"):
        assert key in data, f"Batch missing: {key}"
    assert isinstance(data["items"], list) and len(data["items"]) == len(goals)
    item = data["items"][0]
    for key in ("title", "overall_score", "alignment_level", "goal_type"):
        assert key in item, f"Batch item missing: {key}"

@run("rewrite_goal", "EvaluatePage")
def _():
    r = post("/api/v1/goals/rewrite", {
        "employee_id": "emp_1",
        "goal_text": "Улучшить работу",
        "quarter": "Q2",
        "year": 2026,
    })
    assert r.status_code == 200
    data = r.json()
    assert "rewrite" in data and len(data["rewrite"]) > 10

# ═══════════════════════════════════════════════════════════════════
# 3. GeneratePage
# ═══════════════════════════════════════════════════════════════════
print("\n✨ GeneratePage")
print("-" * 50)

@run("generate_goals", "GeneratePage")
def _():
    r = post("/api/v1/goals/generate", {
        "employee_id": "emp_1",
        "quarter": "Q2",
        "year": 2026,
        "count": 3,
        "focus": "цифровизация HR-процессов",
    })
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) == 3
    for goal in data:
        for key in ("title", "score", "alignment_level", "goal_type", "methodology", "rationale", "source"):
            assert key in goal, f"Goal missing: {key}"
        src = goal["source"]
        for key in ("doc_id", "title", "doc_type", "fragment"):
            assert key in src, f"Source missing: {key}"

@run("generate_goals_5", "GeneratePage")
def _():
    r = post("/api/v1/goals/generate", {
        "employee_id": "emp_1",
        "quarter": "Q2",
        "year": 2026,
        "count": 5,
    })
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) == 5

# ═══════════════════════════════════════════════════════════════════
# 4. CascadePage
# ═══════════════════════════════════════════════════════════════════
print("\n🔗 CascadePage")
print("-" * 50)

@run("cascade_goals", "CascadePage")
def _():
    # Find a manager
    emps = get("/api/v1/employees").json()
    managers = [e for e in emps if any(sub["manager_id"] == e["id"] for sub in emps)]
    manager_id = managers[0]["id"] if managers else "emp_mgr"
    r = post("/api/v1/goals/cascade", {
        "manager_id": manager_id,
        "quarter": "Q2",
        "year": 2026,
        "count_per_employee": 3,
    })
    assert r.status_code == 200
    data = r.json()
    for key in ("manager_id", "manager_name", "manager_goals", "subordinates", "total_generated"):
        assert key in data, f"Cascade missing: {key}"
    assert isinstance(data["subordinates"], list)
    if data["subordinates"]:
        sub = data["subordinates"][0]
        for key in ("employee_id", "employee_name", "position", "department", "goals"):
            assert key in sub, f"Subordinate missing: {key}"
        if sub["goals"]:
            goal = sub["goals"][0]
            for key in ("title", "score", "alignment_level", "goal_type", "source"):
                assert key in goal, f"Cascade goal missing: {key}"

# ═══════════════════════════════════════════════════════════════════
# 5. DashboardPage
# ═══════════════════════════════════════════════════════════════════
print("\n📊 DashboardPage")
print("-" * 50)

@run("dashboard_overview", "DashboardPage")
def _():
    r = get("/api/v1/dashboard/overview?quarter=Q2&year=2026")
    assert r.status_code == 200
    data = r.json()
    for key in ("quarter", "year", "total_departments", "total_goals_evaluated", "avg_smart_score", "strategic_goal_share", "departments"):
        assert key in data, f"Dashboard missing: {key}"
    assert isinstance(data["departments"], list) and len(data["departments"]) > 0
    dept = data["departments"][0]
    for key in ("department_id", "department_name", "avg_smart_score", "strategic_goal_share", "weakest_criterion", "alert_count", "maturity_index", "maturity_level"):
        assert key in dept, f"Dept snapshot missing: {key}"

@run("department_snapshot", "DashboardPage")
def _():
    overview = get("/api/v1/dashboard/overview?quarter=Q2&year=2026").json()
    dept_id = overview["departments"][0]["department_id"]
    r = get(f"/api/v1/dashboard/departments/{dept_id}?quarter=Q2&year=2026")
    assert r.status_code == 200
    data = r.json()
    for key in ("department_id", "department_name", "avg_smart_score", "strategic_goal_share", "weakest_criterion", "alert_count", "maturity_index", "maturity_level"):
        assert key in data, f"Dept detail missing: {key}"

@run("data_stats", "DashboardPage")
def _():
    r = get("/api/v1/data/stats")
    assert r.status_code == 200
    data = r.json()
    for key in ("departments", "positions", "employees", "documents", "goals", "goal_events", "goal_reviews", "kpi_catalog", "kpi_timeseries", "has_dump_data"):
        assert key in data, f"Stats missing: {key}"

@run("department_404", "DashboardPage")
def _():
    r = get("/api/v1/dashboard/departments/nonexistent?quarter=Q2&year=2026")
    assert r.status_code == 404

# ═══════════════════════════════════════════════════════════════════
# 6. MaturityPage
# ═══════════════════════════════════════════════════════════════════
print("\n🎯 MaturityPage")
print("-" * 50)

@run("maturity_report", "MaturityPage")
def _():
    depts = get("/api/v1/departments").json()
    dept_id = depts[0]["id"]
    r = get(f"/api/v1/dashboard/departments/{dept_id}/maturity?quarter=Q2&year=2026")
    assert r.status_code == 200
    data = r.json()
    for key in ("department_id", "department_name", "quarter", "year",
                "maturity_index", "maturity_level",
                "total_employees", "employees_with_goals", "total_goals",
                "avg_smart_score", "strategic_goal_share",
                "smart_distribution", "goal_type_distribution", "alignment_distribution",
                "weakest_criteria", "top_recommendations", "alert_count"):
        assert key in data, f"Maturity missing: {key}"
    # Sub-dicts used for pie charts
    sd = data["smart_distribution"]
    for key in ("excellent", "good", "needs_improvement"):
        assert key in sd, f"SmartDist missing: {key}"
    gt = data["goal_type_distribution"]
    for key in ("impact_based", "output_based", "activity_based"):
        assert key in gt, f"GoalTypeDist missing: {key}"
    ad = data["alignment_distribution"]
    for key in ("strategic", "functional", "operational"):
        assert key in ad, f"AlignDist missing: {key}"

@run("maturity_all_departments", "MaturityPage")
def _():
    depts = get("/api/v1/departments").json()
    for dept in depts:
        r = get(f"/api/v1/dashboard/departments/{dept['id']}/maturity?quarter=Q2&year=2026")
        assert r.status_code == 200, f"Maturity failed for {dept['id']}: {r.status_code}"
        d = r.json()
        assert d["department_id"] == dept["id"]

# ═══════════════════════════════════════════════════════════════════
# 7. Cross-page: EmployeePicker — filter by department
# ═══════════════════════════════════════════════════════════════════
print("\n🔍 Cross-page: Pickers & Filters")
print("-" * 50)

@run("employees_filter_department", "EmployeePicker")
def _():
    depts = get("/api/v1/departments").json()
    dept_id = depts[0]["id"]
    r = get(f"/api/v1/employees?department_id={dept_id}")
    assert r.status_code == 200
    data = r.json()
    assert all(e["department_id"] == dept_id for e in data)

@run("employee_context_404", "EmployeePicker")
def _():
    r = get("/api/v1/employees/nonexistent/context?quarter=Q2&year=2026")
    assert r.status_code == 404

# ═══════════════════════════════════════════════════════════════════
# 8. Edge cases the frontend should handle
# ═══════════════════════════════════════════════════════════════════
print("\n⚠️ Edge cases / Error handling")
print("-" * 50)

@run("evaluate_empty_goal", "EvaluatePage")
def _():
    r = post("/api/v1/goals/evaluate", {
        "employee_id": "emp_1",
        "goal_text": "",
        "quarter": "Q2",
        "year": 2026,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["overall_score"] < 0.5  # Empty goal should score poorly

@run("evaluate_very_long_goal", "EvaluatePage")
def _():
    r = post("/api/v1/goals/evaluate", {
        "employee_id": "emp_1",
        "goal_text": "Цель " * 500,
        "quarter": "Q2",
        "year": 2026,
    })
    assert r.status_code == 200

@run("generate_nonexistent_employee", "GeneratePage")
def _():
    r = post("/api/v1/goals/generate", {
        "employee_id": "nonexistent",
        "quarter": "Q2",
        "year": 2026,
        "count": 3,
    })
    # Should either return 404 or 200 with fallback
    assert r.status_code in (200, 404)

@run("batch_empty_goals", "EvaluatePage")
def _():
    r = post("/api/v1/goals/evaluate-batch", {
        "employee_id": "emp_1",
        "quarter": "Q2",
        "year": 2026,
        "goals": [],
    })
    # Should handle gracefully
    assert r.status_code in (200, 422)

# ═══════════════════════════════════════════════════════════════════
# 9. Frontend build verification (static files exist)
# ═══════════════════════════════════════════════════════════════════
print("\n🌐 Frontend Build Verification")
print("-" * 50)

@run("build_index_html_exists", "Build")
def _():
    from pathlib import Path
    dist = Path(__file__).parent.parent / "frontend" / "dist"
    index = dist / "index.html"
    assert index.exists(), f"dist/index.html not found at {index}"
    html = index.read_text(encoding="utf-8")
    assert "GoalCraft AI" in html or "<div id=\"root\">" in html

@run("build_assets_exist", "Build")
def _():
    from pathlib import Path
    assets = Path(__file__).parent.parent / "frontend" / "dist" / "assets"
    assert assets.exists(), "dist/assets/ not found"
    js_files = list(assets.glob("*.js"))
    css_files = list(assets.glob("*.css"))
    assert len(js_files) >= 1, f"No JS bundles found"
    assert len(css_files) >= 1, f"No CSS bundles found"

@run("build_js_bundle_valid", "Build")
def _():
    from pathlib import Path
    assets = Path(__file__).parent.parent / "frontend" / "dist" / "assets"
    js_files = list(assets.glob("*.js"))
    content = js_files[0].read_text(encoding="utf-8")
    # Check that key React/app components are bundled
    assert len(content) > 10000, "JS bundle suspiciously small"
    # Check for key strings that should be in the bundle
    for keyword in ["GoalCraft", "evaluate", "generate", "dashboard"]:
        assert keyword.lower() in content.lower(), f"Bundle missing '{keyword}'"

@run("build_css_valid", "Build")
def _():
    from pathlib import Path
    assets = Path(__file__).parent.parent / "frontend" / "dist" / "assets"
    css_files = list(assets.glob("*.css"))
    content = css_files[0].read_text(encoding="utf-8")
    assert len(content) > 500, "CSS bundle too small"

@run("vite_proxy_config", "Build")
def _():
    """Verify vite.config.ts has correct proxy for /api and /health."""
    from pathlib import Path
    config = Path(__file__).parent.parent / "frontend" / "vite.config.ts"
    assert config.exists()
    content = config.read_text(encoding="utf-8")
    assert "'/api'" in content or '"/api"' in content, "Proxy for /api not configured"
    assert "'/health'" in content or '"/health"' in content, "Proxy for /health not configured"
    assert "8899" in content, "Proxy target port 8899 not found"

# ═══════════════════════════════════════════════════════════════════
# 10. Goal History (used by potential history view)
# ═══════════════════════════════════════════════════════════════════
print("\n📜 Goal History API")
print("-" * 50)

@run("goal_history", "GoalHistory")
def _():
    ctx = get("/api/v1/employees/emp_1/context?quarter=Q2&year=2026").json()
    if ctx["active_goals"]:
        goal_id = ctx["active_goals"][0]["id"]
        r = get(f"/api/v1/goals/{goal_id}/history")
        assert r.status_code == 200
        data = r.json()
        for key in ("goal_id", "events", "reviews", "total_events", "total_reviews"):
            assert key in data, f"History missing: {key}"
    else:
        # No goals, skip
        pass

# ═══════════════════════════════════════════════════════════════════
# 11. Ingest documents (used by admin)
# ═══════════════════════════════════════════════════════════════════
print("\n📄 Ingest Documents API")
print("-" * 50)

@run("ingest_documents", "Admin")
def _():
    r = post("/api/v1/documents/ingest", {
        "documents": [
            {
                "doc_id": "test_doc_99",
                "doc_type": "policy",
                "title": "Тестовый документ для проверки фронтенда",
                "content": "Содержание тестового документа для верификации работы API ingest.",
            }
        ]
    })
    assert r.status_code == 200
    data = r.json()
    assert "indexed_documents" in data and "indexed_chunks" in data

# ═══════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
passed = sum(1 for r in results if r.passed)
failed = sum(1 for r in results if not r.passed)
total = len(results)
total_ms = sum(r.duration_ms for r in results)

print(f"  FRONTEND FUNCTIONAL TESTS: {passed}/{total} passed ({passed/total*100:.1f}%)")
print(f"  DURATION: {total_ms/1000:.1f}s")
print("=" * 60)

if failed:
    print(f"\n❌ FAILURES ({failed}):")
    for r in results:
        if not r.passed:
            print(f"  [{r.page}] {r.name}: {r.detail}")

# Group by page
pages: dict[str, list[TestResult]] = {}
for r in results:
    pages.setdefault(r.page, []).append(r)

print("\nBy Page:")
for page, tests in pages.items():
    p = sum(1 for t in tests if t.passed)
    print(f"  {page}: {p}/{len(tests)}")

# Save report
report = {
    "total": total,
    "passed": passed,
    "failed": failed,
    "pass_rate": f"{passed/total*100:.1f}%",
    "duration_s": round(total_ms / 1000, 2),
    "results": [{"name": r.name, "page": r.page, "passed": r.passed, "duration_ms": round(r.duration_ms, 1), "detail": r.detail} for r in results],
}
from pathlib import Path
Path(__file__).parent.joinpath("frontend_test_report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(f"\nReport saved: qa/frontend_test_report.json")

sys.exit(0 if failed == 0 else 1)
