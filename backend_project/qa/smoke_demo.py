"""Quick smoke test for all major endpoints (demo mode)."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

tests_passed = 0
tests_failed = 0

def test(name, fn):
    global tests_passed, tests_failed
    try:
        fn()
        print(f"  ✅ {name}")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        tests_failed += 1

def t_health():
    r = client.get("/health")
    assert r.status_code == 200
    h = r.json()
    assert h["status"] == "ok"

def t_departments():
    r = client.get("/api/v1/departments")
    assert r.status_code == 200
    assert len(r.json()) > 0

def t_employees():
    r = client.get("/api/v1/employees")
    assert r.status_code == 200
    assert len(r.json()) > 0

def t_evaluate():
    r = client.post("/api/v1/goals/evaluate", json={
        "employee_id": "emp_1",
        "goal_text": "До конца Q2 довести долю целей до 85%",
        "quarter": "Q2", "year": 2026,
    })
    assert r.status_code == 200
    assert r.json()["overall_score"] > 0

def t_generate():
    r = client.post("/api/v1/goals/generate", json={
        "employee_id": "emp_1", "quarter": "Q2", "year": 2026, "count": 3,
    })
    assert r.status_code == 200
    assert len(r.json()) > 0

def t_dashboard_overview():
    r = client.get("/api/v1/dashboard/overview?quarter=Q2&year=2026")
    assert r.status_code == 200
    ov = r.json()
    assert ov["total_departments"] > 0

def t_dashboard_department():
    depts = client.get("/api/v1/departments").json()
    dept_id = depts[0]["id"]
    r = client.get(f"/api/v1/dashboard/departments/{dept_id}?quarter=Q2&year=2026")
    assert r.status_code == 200

def t_data_stats():
    r = client.get("/api/v1/data/stats")
    assert r.status_code == 200

def t_notifications():
    r = client.get("/api/v1/notifications?quarter=Q2&year=2026")
    assert r.status_code == 200
    n = r.json()
    assert "total" in n

def t_maturity():
    depts = client.get("/api/v1/departments").json()
    dept_id = depts[0]["id"]
    r = client.get(f"/api/v1/dashboard/departments/{dept_id}/maturity?quarter=Q2&year=2026")
    assert r.status_code == 200

def t_evaluate_batch():
    r = client.post("/api/v1/goals/evaluate-batch", json={
        "employee_id": "emp_1", "quarter": "Q2", "year": 2026,
        "goals": [
            {"title": "Довести долю целей до 85%", "weight": 50},
            {"title": "Сократить срок согласования до 3 дней", "weight": 50},
        ],
    })
    assert r.status_code == 200

def t_cascade():
    r = client.post("/api/v1/goals/cascade", json={
        "manager_id": "emp_mgr", "quarter": "Q2", "year": 2026,
        "count_per_employee": 2,
    })
    assert r.status_code == 200

print("Running smoke tests (demo mode)...")
test("Health", t_health)
test("Departments", t_departments)
test("Employees", t_employees)
test("Evaluate goal", t_evaluate)
test("Generate goals", t_generate)
test("Dashboard overview", t_dashboard_overview)
test("Dashboard department", t_dashboard_department)
test("Data stats", t_data_stats)
test("Notifications", t_notifications)
test("Maturity report", t_maturity)
test("Evaluate batch", t_evaluate_batch)
test("Cascade goals", t_cascade)

print(f"\n{tests_passed}/{tests_passed + tests_failed} tests passed")
if tests_failed:
    exit(1)
