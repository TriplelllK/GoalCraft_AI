"""Quick LLM analysis script."""
import requests
import json

BASE = "http://localhost:8899"

# Test generate
r = requests.post(f"{BASE}/api/v1/goals/generate", json={
    "employee_id": "emp_1", "quarter": "Q2", "year": 2026, "count": 3
})
d = r.json()
print("=== GENERATE (3 goals) ===")
for i, g in enumerate(d):
    print(f"  [{i+1}] score={g['score']:.2f} | type={g['goal_type']} | align={g['alignment_level']} | methodology={g.get('methodology','n/a')}")
    print(f"      title: {g['title'][:120]}")
    print()

# Test rewrite on all 3 evaluate cases
cases = [
    "Улучшить процесс обучения сотрудников",
    "До 30.06 сократить средний срок согласования HR-заявок с 5 до 3 рабочих дней за счет цифровизации маршрута согласования",
    "До конца Q2 внедрить дашборд по статусу целей и обязательному обучению с еженедельным обновлением показателей",
]
print("=== REWRITES ===")
for c in cases:
    r2 = requests.post(f"{BASE}/api/v1/goals/evaluate", json={
        "employee_id": "emp_1", "goal_text": c, "quarter": "Q2", "year": 2026
    })
    d2 = r2.json()
    print(f"  score={d2['overall_score']:.2f} | {d2['alignment_level']} | {d2['goal_type']}")
    print(f"  rewrite: {d2['rewrite']}")
    has_marker = "с достижением показателя" in d2["rewrite"]
    print(f"  has 'с достижением показателя': {has_marker}")
    if d2.get("okr_mapping"):
        okr = d2["okr_mapping"]
        print(f"  OKR objective: {okr['objective'][:80]}")
        print(f"  OKR KRs: {len(okr['key_results'])}")
        print(f"  OKR ambition: {okr['ambition_score']}, transparency: {okr['transparency_score']}")
    print()
