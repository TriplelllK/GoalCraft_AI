"""Full LLM integration test — verify all LLM features work correctly."""
import requests
import json
import sys

BASE = "http://localhost:8899"
errors = []
tests_passed = 0
tests_total = 0


def test(name, condition, detail=""):
    global tests_passed, tests_total
    tests_total += 1
    if condition:
        tests_passed += 1
        print(f"  ✅ {name}")
    else:
        errors.append(f"{name}: {detail}")
        print(f"  ❌ {name}: {detail}")


print("=" * 60)
print("ТЕСТ LLM ИНТЕГРАЦИИ")
print("=" * 60)

# 1. Health check
r = requests.get(f"{BASE}/health")
d = r.json()
test("Health: LLM enabled", d["llm_enabled"] is True, f"llm_enabled={d.get('llm_enabled')}")

# 2. Evaluate with OKR mapping
print("\n── Evaluate + OKR ──")
r = requests.post(f"{BASE}/api/v1/goals/evaluate", json={
    "employee_id": "emp_1",
    "goal_text": "Улучшить процесс обучения сотрудников",
    "quarter": "Q2", "year": 2026
})
d = r.json()
test("Evaluate: methodology = SMART+OKR", d.get("methodology") == "SMART+OKR", f"got {d.get('methodology')}")
test("Evaluate: OKR mapping present", d.get("okr_mapping") is not None, "no okr_mapping")
if d.get("okr_mapping"):
    okr = d["okr_mapping"]
    test("OKR: has objective", bool(okr.get("objective")), "no objective")
    test("OKR: has key_results", len(okr.get("key_results", [])) >= 2, f"KRs: {len(okr.get('key_results', []))}")
    test("OKR: ambition_score is numeric", isinstance(okr.get("ambition_score"), (int, float)), f"type: {type(okr.get('ambition_score'))}")
    test("OKR: transparency_score is numeric", isinstance(okr.get("transparency_score"), (int, float)), f"type: {type(okr.get('transparency_score'))}")
    test("OKR: has recommendation", bool(okr.get("okr_recommendation")), "no recommendation")
test("Evaluate: rewrite present", len(d.get("rewrite", "")) > 30, f"rewrite len: {len(d.get('rewrite', ''))}")
test("Evaluate: rewrite has correct year", "2026" in d.get("rewrite", ""), f"rewrite: {d.get('rewrite', '')[:100]}")

# 3. Generate goals with LLM
print("\n── Generate Goals ──")
r = requests.post(f"{BASE}/api/v1/goals/generate", json={
    "employee_id": "emp_1", "quarter": "Q2", "year": 2026, "count": 3
})
d = r.json()
test("Generate: returns 3 goals", len(d) == 3, f"got {len(d)}")
for i, g in enumerate(d):
    test(f"Generate [{i+1}]: score >= 0.7", g["score"] >= 0.7, f"score={g['score']}")
    test(f"Generate [{i+1}]: has methodology", "LLM" in g.get("methodology", ""), f"methodology={g.get('methodology')}")
    test(f"Generate [{i+1}]: title > 30 chars", len(g["title"]) > 30, f"title len={len(g['title'])}")
    print(f"      Title: {g['title'][:100]}")

# 4. Good goal with OKR
print("\n── Good Goal + OKR ──")
r = requests.post(f"{BASE}/api/v1/goals/evaluate", json={
    "employee_id": "emp_1",
    "goal_text": "До 30.06.2026 снизить текучесть персонала с 18% до 12% за счет внедрения программы удержания ключевых сотрудников",
    "quarter": "Q2", "year": 2026
})
d = r.json()
test("Good goal: score >= 0.7", d["overall_score"] >= 0.7, f"score={d['overall_score']}")
test("Good goal: has OKR mapping", d.get("okr_mapping") is not None, "no okr_mapping")
test("Good goal: methodology SMART+OKR", d.get("methodology") == "SMART+OKR", f"got {d.get('methodology')}")

# Summary
print("\n" + "=" * 60)
print(f"ИТОГО: {tests_passed}/{tests_total} тестов пройдено")
if errors:
    print(f"\n❌ ОШИБКИ ({len(errors)}):")
    for e in errors:
        print(f"  • {e}")
print("=" * 60)

sys.exit(0 if not errors else 1)
