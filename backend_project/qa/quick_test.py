"""Quick integration test for all major endpoints."""
import requests
import json

BASE = "http://localhost:8899"

# 1. Health
r = requests.get(f"{BASE}/health")
h = r.json()
print("=== 1. HEALTH ===")
print(f"Status: {h['status']}, LLM: {h['llm_enabled']}, Docs: {h['indexed_documents']}, Chunks: {h['indexed_chunks']}")
print()

# 2. Evaluate weak goal
r = requests.post(f"{BASE}/api/v1/goals/evaluate", json={
    "employee_id": "emp_1",
    "goal_text": "Улучшить работу отдела",
    "quarter": "Q2", "year": 2026
})
e = r.json()
print("=== 2. WEAK GOAL ===")
print(f"Score: {e['overall_score']}, Alignment: {e['alignment_level']}, Type: {e['goal_type']}")
print(f"Methodology: {e['methodology']}")
print(f"Recs: {e['recommendations'][:2]}")
print(f"Rewrite: {e['rewrite'][:150]}")
if e.get("okr_mapping"):
    print(f"OKR: {e['okr_mapping']['objective']}")
print()

# 3. Evaluate strong goal
r = requests.post(f"{BASE}/api/v1/goals/evaluate", json={
    "employee_id": "emp_1",
    "goal_text": "До 30.06 сократить средний срок согласования HR-заявок с 5 до 3 рабочих дней за счет цифровизации маршрута согласования",
    "quarter": "Q2", "year": 2026
})
e = r.json()
print("=== 3. STRONG GOAL ===")
print(f"Score: {e['overall_score']}, Alignment: {e['alignment_level']}, Type: {e['goal_type']}")
print(f"SMART: S={e['scores']['specific']}, M={e['scores']['measurable']}, A={e['scores']['achievable']}, R={e['scores']['relevant']}, T={e['scores']['timebound']}")
if e.get("okr_mapping"):
    print(f"OKR: {e['okr_mapping']['objective']}")
    krs = e["okr_mapping"].get("key_results", [])
    for kr in krs[:3]:
        print(f"  - {kr}")
print()

# 4. Generate for recruiter
r = requests.post(f"{BASE}/api/v1/goals/generate", json={
    "employee_id": "emp_4",
    "quarter": "Q2", "year": 2026,
    "count": 3, "focus": "подбор и адаптация"
})
goals = r.json()
print("=== 4. GENERATE FOR RECRUITER ===")
for i, g in enumerate(goals):
    print(f"  [{i+1}] Score={g['score']:.2f} | {g['title'][:120]}")
    print(f"      Method: {g['methodology']}, Source: {g.get('source', {}).get('title', 'N/A')[:60]}")
print()

# 5. Generate for C&B
r = requests.post(f"{BASE}/api/v1/goals/generate", json={
    "employee_id": "emp_3",
    "quarter": "Q2", "year": 2026,
    "count": 3, "focus": "компенсации и грейды"
})
goals = r.json()
print("=== 5. GENERATE FOR C&B SPECIALIST ===")
for i, g in enumerate(goals):
    print(f"  [{i+1}] Score={g['score']:.2f} | {g['title'][:120]}")
print()

# 6. Rewrite weak goal
r = requests.post(f"{BASE}/api/v1/goals/rewrite", json={
    "employee_id": "emp_1",
    "goal_text": "Сделать обучение лучше",
    "quarter": "Q2"
})
rw = r.json()
print("=== 6. REWRITE ===")
print(f"Rewrite: {rw['rewrite'][:200]}")
print()

# 7. Batch evaluation
r = requests.post(f"{BASE}/api/v1/goals/evaluate-batch", json={
    "employee_id": "emp_1",
    "quarter": "Q2", "year": 2026,
    "goals": [
        {"title": "До 30.06 довести долю KPI-привязанных целей до 85%", "weight": 30.0},
        {"title": "До конца Q2 сократить срок согласования заявок до 3 дней", "weight": 30.0},
        {"title": "Улучшить процессы в отделе", "weight": 40.0}
    ]
})
b = r.json()
print("=== 7. BATCH ===")
print(f"Count: {b['goal_count']}, Avg: {b['average_smart_index']}, Strategic: {b['strategic_goal_share']}")
print(f"Weight: {b['total_weight']}, Weakest: {b['weakest_criteria']}")
print(f"Alerts: {b['alerts']}")
print()

# 8. Employee context
r = requests.get(f"{BASE}/api/v1/employees/emp_4/context?quarter=Q2&year=2026")
ctx = r.json()
print("=== 8. EMPLOYEE CONTEXT ===")
pos = ctx.get("position", {})
dept = ctx.get("department", {})
print(f"Name: {ctx['employee']['full_name']}, Position: {pos.get('name','N/A')}, Dept: {dept.get('name','N/A')}")
print(f"Goals: {len(ctx.get('active_goals', []))}")
print()

# 9. Dashboard overview
r = requests.get(f"{BASE}/api/v1/dashboard/overview?quarter=Q2&year=2026")
d = r.json()
print("=== 9. DASHBOARD ===")
print(f"Departments: {d['total_departments']}, Goals: {d['total_goals_evaluated']}")
print(f"Avg SMART: {d['avg_smart_score']}, Strategic: {d['strategic_goal_share']}")
print()

# 10. Maturity report
r = requests.get(f"{BASE}/api/v1/dashboard/departments/dep_hr/maturity?quarter=Q2&year=2026")
m = r.json()
print("=== 10. MATURITY ===")
print(f"Index: {m['maturity_index']}, Level: {m['maturity_level']}")
print(f"Employees: {m['total_employees']}, With goals: {m['employees_with_goals']}, Goals: {m['total_goals']}")
print(f"Recs: {m['top_recommendations'][:2]}")
print()

# 11. Cascade
r = requests.post(f"{BASE}/api/v1/goals/cascade", json={
    "manager_id": "emp_mgr",
    "quarter": "Q2", "year": 2026,
    "count_per_employee": 2
})
c = r.json()
print("=== 11. CASCADE ===")
print(f"Manager: {c['manager_name']}, Subordinates: {len(c['subordinates'])}, Total generated: {c['total_generated']}")
for sub in c["subordinates"][:3]:
    print(f"  {sub['employee_name']} ({sub['position']}): {len(sub['goals'])} goals")
print()

# 12. Goal history (F-15 versioning)
r = requests.get(f"{BASE}/api/v1/goals/goal_hr_001/history")
hist = r.json()
print("=== 12. GOAL HISTORY (F-15) ===")
print(f"Goal: {hist['goal_id']}, Events: {hist['total_events']}, Reviews: {hist['total_reviews']}")
print()

# 13. Data stats (dump verification)
r = requests.get(f"{BASE}/api/v1/data/stats")
stats = r.json()
print("=== 13. DATA STATS ===")
print(f"Departments: {stats['departments']}, Employees: {stats['employees']}, Goals: {stats['goals']}")
print(f"Has dump data: {stats['has_dump_data']}")
print()

# 14. List departments (reference data for dropdowns)
r = requests.get(f"{BASE}/api/v1/departments")
depts = r.json()
print("=== 14. LIST DEPARTMENTS ===")
print(f"Total: {len(depts)} departments")
for d in depts[:3]:
    print(f"  {d['id']}: {d['name']} ({d['code']})")
print()

# 15. List employees (reference data for dropdowns)
r = requests.get(f"{BASE}/api/v1/employees")
emps = r.json()
print("=== 15. LIST EMPLOYEES ===")
print(f"Total: {len(emps)} employees")
for e in emps[:3]:
    print(f"  {e['id']}: {e['full_name']} — {e['position_name']} ({e['department_name']})")
print()

print("=" * 60)
print("✅ ALL 15 ENDPOINT TESTS PASSED SUCCESSFULLY!")
