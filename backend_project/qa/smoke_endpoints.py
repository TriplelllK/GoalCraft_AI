"""Quick 17-endpoint verification — one request per endpoint."""
import requests, sys

BASE = "http://localhost:8899"
ok = 0
fail = 0


def check(label, method, url, payload=None, expect_keys=None, extra=None):
    """Send one request, verify status 200 and optional keys."""
    global ok, fail
    try:
        if method == "GET":
            r = requests.get(url, timeout=30)
        else:
            r = requests.post(url, json=payload, timeout=30)
        if r.status_code != 200:
            raise Exception(f"status {r.status_code}")
        body = r.json()
        if expect_keys:
            for k in expect_keys:
                if k not in body:
                    raise Exception(f"missing key '{k}'")
        if extra:
            extra(body)
        print(f"  ✅ {label}")
        ok += 1
    except Exception as e:
        print(f"  ❌ {label}: {e}")
        fail += 1


print("\n=== Backend: All 17 Endpoints Smoke Test ===\n")

# 1
check("GET /health", "GET", f"{BASE}/health",
      expect_keys=["status"])

# 2
check("GET /departments", "GET", f"{BASE}/api/v1/departments",
      extra=lambda b: (_ for _ in ()).throw(Exception("empty")) if len(b) < 1 else None)

# 3
check("GET /employees", "GET", f"{BASE}/api/v1/employees",
      extra=lambda b: (_ for _ in ()).throw(Exception("empty")) if len(b) < 1 else None)

# 4
check("GET /employees?department_id", "GET",
      f"{BASE}/api/v1/employees?department_id=dep_hr")

# 5
check("GET /employees/{id}/context", "GET",
      f"{BASE}/api/v1/employees/emp_1/context?quarter=Q2&year=2026",
      expect_keys=["employee"])

# 6
check("POST /goals/evaluate", "POST",
      f"{BASE}/api/v1/goals/evaluate",
      payload={"employee_id": "emp_1",
               "goal_text": "Увеличить выручку на 15% к Q3",
               "quarter": "Q2", "year": 2026},
      expect_keys=["overall_score"])

# 7
check("POST /goals/rewrite", "POST",
      f"{BASE}/api/v1/goals/rewrite",
      payload={"employee_id": "emp_1",
               "goal_text": "Улучшить работу",
               "quarter": "Q2", "year": 2026},
      expect_keys=["rewrite"])

# 8
check("POST /goals/generate", "POST",
      f"{BASE}/api/v1/goals/generate",
      payload={"employee_id": "emp_1",
               "quarter": "Q2", "year": 2026, "count": 3},
      extra=lambda b: None if len(b) == 3 else (_ for _ in ()).throw(Exception(f"expected 3, got {len(b)}")))

# 9
check("POST /goals/evaluate-batch", "POST",
      f"{BASE}/api/v1/goals/evaluate-batch",
      payload={"employee_id": "emp_1", "quarter": "Q2", "year": 2026,
               "goals": [{"title": "Test 1", "weight": 50},
                          {"title": "Test 2", "weight": 50}]},
      expect_keys=["average_smart_index"])

# 10
check("POST /goals/cascade", "POST",
      f"{BASE}/api/v1/goals/cascade",
      payload={"manager_id": "emp_mgr", "quarter": "Q2",
               "year": 2026, "count_per_employee": 2},
      expect_keys=["total_generated"])

# 11
check("GET /dashboard/overview", "GET",
      f"{BASE}/api/v1/dashboard/overview?quarter=Q2&year=2026",
      expect_keys=["departments"])

# 12
check("GET /dashboard/departments/{id}", "GET",
      f"{BASE}/api/v1/dashboard/departments/dep_hr?quarter=Q2&year=2026",
      expect_keys=["maturity_level"])

# 13
check("GET /dashboard/departments/{id}/maturity", "GET",
      f"{BASE}/api/v1/dashboard/departments/dep_hr/maturity?quarter=Q2&year=2026",
      expect_keys=["maturity_index"])

# 14
check("GET /goals/{id}/history", "GET",
      f"{BASE}/api/v1/goals/goal_hr_001/history",
      expect_keys=["goal_id"])

# 15
check("GET /data/stats", "GET",
      f"{BASE}/api/v1/data/stats",
      expect_keys=["employees"])

# 16
check("GET /notifications", "GET",
      f"{BASE}/api/v1/notifications?quarter=Q2&year=2026",
      expect_keys=["items"])

# 17
check("POST /documents/ingest", "POST",
      f"{BASE}/api/v1/documents/ingest",
      payload={"documents": [{"doc_id": "smoke_99", "doc_type": "policy",
                               "title": "Smoke", "content": "Smoke test doc"}]},
      expect_keys=["indexed_documents"])

print(f"\n{'=' * 50}")
print(f"  {ok}/{ok + fail} endpoints OK")
print(f"{'=' * 50}")
sys.exit(0 if fail == 0 else 1)
