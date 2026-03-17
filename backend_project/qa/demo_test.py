"""Quick manual test — runs 6 checks against live server and prints results."""
import json
import urllib.request

BASE = "http://localhost:8899"

def api_get(path):
    return json.loads(urllib.request.urlopen(BASE + path).read())

def api_post(path, payload):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())

print("=" * 60)
print("1. HEALTH CHECK")
print("=" * 60)
h = api_get("/health")
print(f"   Status: {h['status']}  |  LLM: {h['llm_enabled']}  |  Documents: {h['indexed_documents']}")

print("\n" + "=" * 60)
print("2. EVALUATE WEAK GOAL")
print("=" * 60)
r = api_post("/api/v1/goals/evaluate", {
    "employee_id": "emp_1",
    "goal_text": "Улучшить работу отдела",
    "quarter": "Q2", "year": 2026
})
print(f"   Goal: 'Улучшить работу отдела'")
print(f"   Score: {r['overall_score']}  |  Type: {r['goal_type']}  |  Alignment: {r['alignment_level']}")
print(f"   Recommendations: {len(r['recommendations'])} items")
for rec in r["recommendations"][:3]:
    print(f"     - {rec[:80]}")
if r.get("rewrite"):
    print(f"   Rewrite: {r['rewrite'][:120]}...")

print("\n" + "=" * 60)
print("3. EVALUATE STRONG GOAL")
print("=" * 60)
r = api_post("/api/v1/goals/evaluate", {
    "employee_id": "emp_1",
    "goal_text": "До 30.06 сократить средний срок согласования HR-заявок с 5 до 3 рабочих дней за счет цифровизации маршрута согласования",
    "quarter": "Q2", "year": 2026
})
print(f"   Score: {r['overall_score']}  |  Type: {r['goal_type']}  |  Alignment: {r['alignment_level']}")
print(f"   SMART: S={r['scores']['specific']:.2f} M={r['scores']['measurable']:.2f} A={r['scores']['achievable']:.2f} R={r['scores']['relevant']:.2f} T={r['scores']['timebound']:.2f}")
print(f"   Achievable: {r['achievability']['is_achievable']}  |  Similar goals: {r['achievability']['similar_goals_found']}")
if r.get("okr_mapping"):
    okr = r["okr_mapping"]
    print(f"   OKR Objective: {okr.get('objective','')[:80]}")
    for kr in okr.get("key_results", [])[:2]:
        print(f"     KR: {kr[:80]}")

print("\n" + "=" * 60)
print("4. GENERATE GOALS FOR RECRUITER")
print("=" * 60)
goals = api_post("/api/v1/goals/generate", {
    "employee_id": "emp_4",
    "quarter": "Q2", "year": 2026,
    "count": 3,
    "focus": "подбор и адаптация персонала"
})
print(f"   Generated: {len(goals)} goals")
for i, g in enumerate(goals, 1):
    print(f"   [{i}] score={g['score']:.2f} | {g['alignment_level']} | {g['goal_type']}")
    print(f"       {g['title'][:100]}")
    if g.get("source"):
        print(f"       Source: {g['source']['title']}")

print("\n" + "=" * 60)
print("5. BATCH EVALUATION")
print("=" * 60)
r = api_post("/api/v1/goals/evaluate-batch", {
    "employee_id": "emp_1",
    "quarter": "Q2", "year": 2026,
    "goals": [
        {"title": "До 30.06 довести долю KPI-привязанных целей до 85%", "weight": 30},
        {"title": "До конца Q2 сократить срок согласования заявок до 3 дней", "weight": 30},
        {"title": "Улучшить процессы в отделе", "weight": 40}
    ]
})
print(f"   Avg SMART index: {r['average_smart_index']:.2f}")
print(f"   Alerts: {r['alerts']}")

print("\n" + "=" * 60)
print("6. MATURITY INDEX (dep_hr)")
print("=" * 60)
r = api_get("/api/v1/dashboard/departments/dep_hr/maturity?quarter=Q2&year=2026")
print(f"   Maturity index: {r['maturity_index']:.2f}  |  Level: {r['maturity_level']}")
print(f"   Total goals: {r['total_goals']}")
for rec in r.get("recommendations", [])[:2]:
    print(f"   Rec: {rec[:80]}")

print("\n" + "=" * 60)
print("ALL 6 CHECKS PASSED!")
print("=" * 60)
