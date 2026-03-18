"""
Live backend integration tests — runs against localhost:8080.
Tests all API endpoints for correct schema, status codes, and response quality.

Usage:
    cd backend_project
    python -X utf8 qa/test_live_backend.py
"""
import sys
import requests
from typing import Any, Optional

BASE = "http://localhost:8080"
PASS: list[str] = []
FAIL: list[str] = []
WARN: list[str] = []

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


def ok(name: str, detail: str = ""):
    print(f"  {GREEN}PASS{RESET}  {name}" + (f"  ({detail})" if detail else ""))
    PASS.append(name)

def fail(name: str, detail: str = ""):
    print(f"  {RED}FAIL{RESET}  {name}" + (f"  ({detail})" if detail else ""))
    FAIL.append(name)

def warn(name: str, detail: str = ""):
    print(f"  {YELLOW}WARN{RESET}  {name}" + (f"  ({detail})" if detail else ""))
    WARN.append(name)

def section(title: str):
    print(f"\n{BOLD}{'-'*60}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{BOLD}{'-'*60}{RESET}")

def safe_get(path: str, timeout: int = 30) -> Optional[Any]:
    """GET request — returns parsed JSON or None on error."""
    try:
        r = requests.get(f"{BASE}{path}", timeout=timeout)
        if r.status_code == 200:
            return r.json()
        fail(f"HTTP GET {path}", f"status={r.status_code} {r.text[:100]}")
        return None
    except requests.exceptions.Timeout:
        fail(f"HTTP GET {path}", f"timed out after {timeout}s")
        return None
    except Exception as e:
        fail(f"HTTP GET {path}", str(e)[:100])
        return None

def safe_post(path: str, payload: dict, timeout: int = 60) -> Optional[Any]:
    """POST request — returns parsed JSON or None on error."""
    try:
        r = requests.post(f"{BASE}{path}", json=payload, timeout=timeout)
        if r.status_code == 200:
            return r.json()
        fail(f"HTTP POST {path}", f"status={r.status_code} {r.text[:100]}")
        return None
    except requests.exceptions.Timeout:
        warn(f"HTTP POST {path}", f"timed out after {timeout}s (LLM-heavy op)")
        return None
    except Exception as e:
        fail(f"HTTP POST {path}", str(e)[:100])
        return None

def check_keys(data: dict, keys: list[str], name: str) -> bool:
    missing = [k for k in keys if k not in data]
    if missing:
        fail(name, f"missing keys: {missing}")
        return False
    ok(name)
    return True


# ─────────────────────────────────────────────────────────────
# §1  Health check
# ─────────────────────────────────────────────────────────────
section("1. Health check")

h = safe_get("/health")
if h is None:
    print(f"\n{RED}Cannot reach {BASE} — is the backend running?{RESET}")
    sys.exit(1)

ok("health.status_200")
check_keys(h, ["status", "mode", "vector_backend", "indexed_documents",
               "indexed_chunks", "llm_enabled", "employees_count", "goals_count"],
           "health.schema")

if h.get("status") == "ok":
    ok("health.status_ok")
else:
    fail("health.status_ok", h.get("status"))

if h.get("mode") == "hackathon-dump":
    ok("health.hackathon_mode")
else:
    warn("health.hackathon_mode", f"mode={h.get('mode')}")

emp_count = h.get("employees_count", 0)
if emp_count >= 400:
    ok("health.employees_count", f"{emp_count} employees")
else:
    fail("health.employees_count", f"only {emp_count}")

goals_count = h.get("goals_count", 0)
if goals_count >= 9000:
    ok("health.goals_count", f"{goals_count} goals")
else:
    warn("health.goals_count", f"only {goals_count}")

if h.get("llm_enabled"):
    ok("health.llm_enabled")
else:
    warn("health.llm_enabled", "LLM disabled")

print(f"    mode={h.get('mode')}, vector={h.get('vector_backend')}, "
      f"docs={h.get('indexed_documents')}, chunks={h.get('indexed_chunks')}")

# ─────────────────────────────────────────────────────────────
# §2  Reference data
# ─────────────────────────────────────────────────────────────
section("2. Reference data")

DEPT_ID = None
EMP_ID = None
EMP_NAME = ""
MANAGER_ID = None

depts = safe_get("/api/v1/departments")
if depts:
    if len(depts) > 0:
        ok("departments.list", f"{len(depts)} departments")
        check_keys(depts[0], ["id", "name", "code"], "departments.schema")
        DEPT_ID = depts[0]["id"]
    else:
        fail("departments.list", "empty")

employees = safe_get("/api/v1/employees")
if employees:
    if len(employees) >= 400:
        ok("employees.list", f"{len(employees)} employees")
    else:
        fail("employees.list", f"only {len(employees)}")
    check_keys(employees[0], ["id", "full_name", "department_id", "department_name",
                              "position_id", "position_name"], "employees.schema")
    EMP_ID = employees[0]["id"]
    EMP_NAME = employees[0]["full_name"]
    mgr_emps = [e for e in employees if e.get("manager_id")]
    MANAGER_ID = mgr_emps[0]["manager_id"] if mgr_emps else None

if DEPT_ID:
    dept_emps = safe_get(f"/api/v1/employees?department_id={DEPT_ID}")
    if dept_emps is not None:
        if len(dept_emps) > 0:
            ok("employees.filter_by_dept", f"{len(dept_emps)} in dept {DEPT_ID[:8]}")
        else:
            warn("employees.filter_by_dept", "0 employees in dept")

stats = safe_get("/api/v1/data/stats")
if stats:
    check_keys(stats, ["departments", "positions", "employees", "documents",
                       "goals", "goal_events", "goal_reviews", "kpi_catalog",
                       "kpi_timeseries", "has_dump_data"], "data_stats.schema")
    if stats.get("has_dump_data"):
        ok("data_stats.has_dump_data")
    else:
        warn("data_stats.has_dump_data", "dump not detected")
    print(f"    depts={stats.get('departments')}, emps={stats.get('employees')}, "
          f"goals={stats.get('goals')}, kpi_ts={stats.get('kpi_timeseries')}")

# ─────────────────────────────────────────────────────────────
# §3  Employee context
# ─────────────────────────────────────────────────────────────
section("3. Employee context")

GOAL_ID = None
if EMP_ID:
    ctx = safe_get(f"/api/v1/employees/{EMP_ID}/context?quarter=Q2&year=2026")
    if ctx:
        ok("employee_context.status_200")
        check_keys(ctx, ["employee", "active_goals"], "employee_context.schema")
        emp_obj = ctx.get("employee", {})
        if emp_obj.get("id") == EMP_ID:
            ok("employee_context.correct_employee", emp_obj.get("full_name", "")[:30])
        else:
            fail("employee_context.correct_employee")
        goals = ctx.get("active_goals", [])
        ok("employee_context.active_goals", f"{len(goals)} goals")
        if goals:
            GOAL_ID = goals[0].get("id")
else:
    warn("employee_context", "no employee id")

# ─────────────────────────────────────────────────────────────
# §4  Goal evaluation
# ─────────────────────────────────────────────────────────────
section("4. Goal evaluation")

IT_GOAL = "Снизить MTTR c 12 часов до 8 часов за Q2 2026, внедрив автоматизированный мониторинг и алертинг в Grafana"
WEAK_GOAL = "Улучшить работу"

if EMP_ID:
    ev = safe_post("/api/v1/goals/evaluate", {
        "employee_id": EMP_ID,
        "goal_text": IT_GOAL,
        "quarter": "Q2",
        "year": 2026,
    })
    if ev:
        ok("evaluate.status_200")
        check_keys(ev, ["scores", "overall_score", "alignment_level",
                        "goal_type", "methodology", "recommendations", "rewrite"],
                   "evaluate.schema")
        scores = ev.get("scores", {})
        check_keys(scores, ["specific", "measurable", "achievable", "relevant", "timebound"],
                   "evaluate.smart_scores_schema")
        overall = ev.get("overall_score", 0)
        if overall >= 0.6:
            ok("evaluate.smart_score_quality", f"overall={overall:.2f} >= 0.60")
        elif overall >= 0.4:
            warn("evaluate.smart_score_quality", f"overall={overall:.2f} < 0.60")
        else:
            fail("evaluate.smart_score_quality", f"overall={overall:.2f} too low")

        alignment = ev.get("alignment_level", "")
        if alignment in ("strategic", "functional"):
            ok("evaluate.alignment_level", f"'{alignment}'")
        else:
            warn("evaluate.alignment_level", f"'{alignment}' — expected strategic/functional for IT MTTR goal")

        goal_type = ev.get("goal_type", "")
        ok("evaluate.goal_type", f"'{goal_type}'")

        if len(ev.get("recommendations", [])) > 0:
            ok("evaluate.recommendations", f"{len(ev['recommendations'])} items")
        else:
            warn("evaluate.recommendations", "empty")

        rewrite = ev.get("rewrite", "")
        if len(rewrite) > 20:
            ok("evaluate.rewrite", f"'{rewrite[:60]}...'")
        else:
            warn("evaluate.rewrite", "short/missing rewrite")

        ach = ev.get("achievability")
        if ach:
            ok("evaluate.achievability_present", f"is_achievable={ach.get('is_achievable')}, conf={ach.get('confidence',0):.2f}")
        else:
            warn("evaluate.achievability", "missing")

        okr = ev.get("okr_mapping")
        if okr:
            ok("evaluate.okr_mapping_present", f"ambition={okr.get('ambition_score',0):.2f}")
        else:
            warn("evaluate.okr_mapping", "missing")

        print(f"    SMART={overall:.2f}, align={alignment}, type={goal_type}")
        for crit, val in scores.items():
            bar = "#" * int(val * 10)
            print(f"      {crit:<12} {val:.2f}  {bar}")

    ev2 = safe_post("/api/v1/goals/evaluate", {
        "employee_id": EMP_ID, "goal_text": WEAK_GOAL, "quarter": "Q2", "year": 2026,
    })
    if ev2:
        overall2 = ev2.get("overall_score", 0)
        it_overall = ev.get("overall_score", 1) if ev else 1
        if overall2 < it_overall:
            ok("evaluate.weak_goal_scored_lower", f"weak={overall2:.2f} < IT={it_overall:.2f}")
        else:
            warn("evaluate.weak_goal_scored_lower", f"weak={overall2:.2f} vs IT={it_overall:.2f}")
else:
    warn("evaluate", "no employee id")

# ─────────────────────────────────────────────────────────────
# §5  Goal rewrite
# ─────────────────────────────────────────────────────────────
section("5. Goal rewrite")

if EMP_ID:
    rw = safe_post("/api/v1/goals/rewrite", {
        "employee_id": EMP_ID, "goal_text": WEAK_GOAL, "quarter": "Q2", "year": 2026,
    })
    if rw:
        if "rewrite" in rw:
            ok("rewrite.schema")
            rewrite_text = rw["rewrite"]
            if len(rewrite_text) > len(WEAK_GOAL):
                ok("rewrite.longer_than_original", f"'{rewrite_text[:80]}...'")
            else:
                warn("rewrite.longer_than_original", "same or shorter")
        else:
            fail("rewrite.schema", f"no 'rewrite' key, got {list(rw.keys())}")
else:
    warn("rewrite", "no employee id")

# ─────────────────────────────────────────────────────────────
# §6  Goal generation
# ─────────────────────────────────────────────────────────────
section("6. Goal generation")

if EMP_ID:
    goals_gen = safe_post("/api/v1/goals/generate", {
        "employee_id": EMP_ID, "quarter": "Q2", "year": 2026, "count": 3,
    })
    if goals_gen is not None:
        if isinstance(goals_gen, list) and len(goals_gen) >= 1:
            ok("generate.list_returned", f"{len(goals_gen)} goals")
            g0 = goals_gen[0]
            check_keys(g0, ["title", "score", "alignment_level", "goal_type",
                            "methodology", "rationale", "source"], "generate.goal_schema")
            avg_score = sum(g.get("score", 0) for g in goals_gen) / len(goals_gen)
            if avg_score >= 0.5:
                ok("generate.avg_score", f"avg={avg_score:.2f}")
            else:
                warn("generate.avg_score", f"avg={avg_score:.2f} — may be weak")
            goals_with_src = [g for g in goals_gen if g.get("source") and g["source"].get("doc_id")]
            if goals_with_src:
                ok("generate.source_references", f"{len(goals_with_src)}/{len(goals_gen)} have sources")
            else:
                warn("generate.source_references", "no source references")
            for g in goals_gen:
                print(f"    [{g.get('alignment_level','?')}] {g.get('title','')[:65]}  score={g.get('score',0):.2f}")
        else:
            fail("generate.list_returned", f"unexpected: {type(goals_gen)}")
else:
    warn("generate", "no employee id")

# ─────────────────────────────────────────────────────────────
# §7  Batch evaluation
# ─────────────────────────────────────────────────────────────
section("7. Batch evaluation")

BATCH_GOALS = [
    {"title": "Снизить MTTR с 12ч до 8ч за Q2 2026 через автоматизированный мониторинг в Grafana", "weight": 0.3},
    {"title": "Провести 5 ретроспектив командой до конца квартала", "weight": 0.2},
    {"title": "Улучшить работу", "weight": 0.5},
]

if EMP_ID:
    batch = safe_post("/api/v1/goals/evaluate-batch", {
        "employee_id": EMP_ID, "quarter": "Q2", "year": 2026, "goals": BATCH_GOALS,
    })
    if batch:
        ok("batch.status_200")
        check_keys(batch, ["goal_count", "average_smart_index", "strategic_goal_share",
                           "weakest_criteria", "duplicates_found", "alerts", "items"], "batch.schema")
        if batch.get("goal_count") == len(BATCH_GOALS):
            ok("batch.goal_count", f"{batch['goal_count']}")
        else:
            warn("batch.goal_count", f"expected {len(BATCH_GOALS)}, got {batch.get('goal_count')}")
        items = batch.get("items", [])
        if len(items) == len(BATCH_GOALS):
            ok("batch.items_count", f"{len(items)}")
        else:
            fail("batch.items_count", f"expected {len(BATCH_GOALS)}, got {len(items)}")
        if len(items) >= 3:
            it_score = items[0].get("overall_score", 0)
            weak_score = items[2].get("overall_score", 0)
            if it_score > weak_score:
                ok("batch.ranking_correct", f"IT={it_score:.2f} > weak={weak_score:.2f}")
            else:
                warn("batch.ranking_correct", f"IT={it_score:.2f} vs weak={weak_score:.2f}")
        print(f"    avg_smart={batch.get('average_smart_index',0):.2f}, "
              f"strategic={batch.get('strategic_goal_share',0):.2f}, "
              f"weakest={batch.get('weakest_criteria')}")
else:
    warn("batch", "no employee id")

# ─────────────────────────────────────────────────────────────
# §8  Dashboard overview
# ─────────────────────────────────────────────────────────────
section("8. Dashboard overview")

overview = safe_get("/api/v1/dashboard/overview?quarter=Q2&year=2026")
if overview:
    ok("dashboard_overview.status_200")
    check_keys(overview, ["quarter", "year", "total_departments", "total_goals_evaluated",
                          "avg_smart_score", "strategic_goal_share", "departments"],
               "dashboard_overview.schema")
    depts_snap = overview.get("departments", [])
    if len(depts_snap) > 0:
        ok("dashboard_overview.departments_populated", f"{len(depts_snap)} dept snapshots")
    else:
        warn("dashboard_overview.departments_populated", "no snapshots")
    avg = overview.get("avg_smart_score", 0)
    ok("dashboard_overview.avg_smart_score", f"{avg:.2f}")
    print(f"    total_depts={overview.get('total_departments')}, "
          f"total_goals={overview.get('total_goals_evaluated')}, "
          f"avg_smart={avg:.2f}, strategic={overview.get('strategic_goal_share',0):.2f}")

# ─────────────────────────────────────────────────────────────
# §9  Department dashboard snapshot
# ─────────────────────────────────────────────────────────────
section("9. Department dashboard snapshot")

if DEPT_ID:
    snap = safe_get(f"/api/v1/dashboard/departments/{DEPT_ID}?quarter=Q2&year=2026")
    if snap:
        ok("dept_dashboard.status_200")
        check_keys(snap, ["department_id", "department_name", "avg_smart_score",
                          "strategic_goal_share", "weakest_criterion", "alert_count",
                          "maturity_index", "maturity_level"], "dept_dashboard.schema")
        print(f"    dept={snap.get('department_name','')[:30]}, "
              f"avg_smart={snap.get('avg_smart_score',0):.2f}, "
              f"maturity={snap.get('maturity_level')}, "
              f"alerts={snap.get('alert_count')}")
else:
    warn("dept_dashboard", "no dept id")

# ─────────────────────────────────────────────────────────────
# §10  Maturity report
# ─────────────────────────────────────────────────────────────
section("10. Maturity report")

if DEPT_ID:
    mat = safe_get(f"/api/v1/dashboard/departments/{DEPT_ID}/maturity?quarter=Q2&year=2026")
    if mat:
        ok("maturity.status_200")
        required = ["department_id", "department_name", "quarter", "year",
                    "maturity_index", "maturity_level", "total_employees",
                    "employees_with_goals", "total_goals", "avg_smart_score",
                    "strategic_goal_share", "smart_distribution",
                    "goal_type_distribution", "alignment_distribution",
                    "weakest_criteria", "top_recommendations", "alert_count"]
        check_keys(mat, required, "maturity.schema")
        check_keys(mat.get("smart_distribution", {}), ["excellent", "good", "needs_improvement"],
                   "maturity.smart_distribution_schema")
        check_keys(mat.get("goal_type_distribution", {}), ["impact_based", "output_based", "activity_based"],
                   "maturity.goal_type_distribution_schema")
        check_keys(mat.get("alignment_distribution", {}), ["strategic", "functional", "operational"],
                   "maturity.alignment_distribution_schema")
        level = mat.get("maturity_level", "")
        if level in ("начальный", "развивающийся", "зрелый", "продвинутый"):
            ok("maturity.valid_level", f"'{level}'")
        else:
            warn("maturity.valid_level", f"'{level}' unexpected")
        print(f"    maturity={level} ({mat.get('maturity_index',0):.2f}), "
              f"employees={mat.get('total_employees')}, "
              f"goals={mat.get('total_goals')}, avg_smart={mat.get('avg_smart_score',0):.2f}")
else:
    warn("maturity", "no dept id")

# ─────────────────────────────────────────────────────────────
# §11  Goal cascade (may be slow with LLM)
# ─────────────────────────────────────────────────────────────
section("11. Goal cascade")

if MANAGER_ID:
    print(f"    Sending cascade request (timeout=120s, LLM-heavy)...")
    casc = safe_post("/api/v1/goals/cascade", {
        "manager_id": MANAGER_ID,
        "quarter": "Q2",
        "year": 2026,
        "count_per_employee": 2,
    }, timeout=120)
    if casc:
        ok("cascade.status_200")
        check_keys(casc, ["manager_id", "manager_name", "manager_goals",
                          "subordinates", "total_generated"], "cascade.schema")
        subs = casc.get("subordinates", [])
        total_gen = casc.get("total_generated", 0)
        if len(subs) > 0:
            ok("cascade.subordinates", f"{len(subs)} subordinates")
        else:
            warn("cascade.subordinates", "no subordinates")
        if total_gen > 0:
            ok("cascade.total_generated", f"{total_gen} goals")
        else:
            warn("cascade.total_generated", "0 goals")
        if subs:
            sub0 = subs[0]
            check_keys(sub0, ["employee_id", "employee_name", "position", "department", "goals"],
                       "cascade.subordinate_schema")
            sub_goals = sub0.get("goals", [])
            if sub_goals:
                check_keys(sub_goals[0], ["title", "score", "alignment_level", "goal_type", "rationale", "source"],
                           "cascade.goal_schema")
        print(f"    manager={casc.get('manager_name','')[:30]}, "
              f"subs={len(subs)}, total_goals={total_gen}")
    # None returned on timeout — already warned by safe_post
else:
    warn("cascade", "no manager_id — skipping")

# ─────────────────────────────────────────────────────────────
# §12  Goal history
# ─────────────────────────────────────────────────────────────
section("12. Goal history")

if GOAL_ID:
    hist = safe_get(f"/api/v1/goals/{GOAL_ID}/history")
    if hist:
        ok("goal_history.status_200")
        check_keys(hist, ["goal_id", "events", "reviews", "total_events", "total_reviews"],
                   "goal_history.schema")
        print(f"    goal_id={GOAL_ID}, events={hist.get('total_events')}, "
              f"reviews={hist.get('total_reviews')}")
else:
    warn("goal_history", "no goal id — skipping")

# ─────────────────────────────────────────────────────────────
# §13  Notifications
# ─────────────────────────────────────────────────────────────
section("13. Notifications")

notifs = safe_get("/api/v1/notifications?quarter=Q2&year=2026")
if notifs:
    ok("notifications.status_200")
    check_keys(notifs, ["total", "critical", "warnings", "info", "items"],
               "notifications.schema")
    total_n = notifs.get("total", 0)
    ok("notifications.total", f"{total_n} alerts")
    if notifs.get("items"):
        n0 = notifs["items"][0]
        check_keys(n0, ["id", "severity", "target_role", "employee_name",
                        "department_id", "department_name", "title", "message",
                        "quarter", "year"], "notifications.item_schema")
    print(f"    total={total_n}, critical={notifs.get('critical')}, "
          f"warnings={notifs.get('warnings')}, info={notifs.get('info')}")

# ─────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────
section("SUMMARY")

total = len(PASS) + len(FAIL) + len(WARN)
print(f"\n  Total checks : {total}")
print(f"  {GREEN}PASS{RESET}         : {len(PASS)}")
print(f"  {YELLOW}WARN{RESET}         : {len(WARN)}")
print(f"  {RED}FAIL{RESET}         : {len(FAIL)}")

if FAIL:
    print(f"\n  {RED}FAILED:{RESET}")
    for f in FAIL:
        print(f"    - {f}")
if WARN:
    print(f"\n  {YELLOW}Warnings:{RESET}")
    for w in WARN:
        print(f"    - {w}")

print()
if not FAIL:
    print(f"  {GREEN}{BOLD}All checks passed!{RESET}")
    sys.exit(0)
else:
    print(f"  {RED}{BOLD}{len(FAIL)} check(s) failed.{RESET}")
    sys.exit(1)
