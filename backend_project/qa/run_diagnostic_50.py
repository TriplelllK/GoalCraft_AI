"""
Diagnostic test: evaluate 50 bad + 50 good goals and produce an accuracy report.
Runs against the live API on port 8899.
"""
import json
import sys
import requests

BASE = "http://localhost:8899"
EMPLOYEE = "emp_1"
QUARTER = "Q2"
YEAR = 2026

# Thresholds
BAD_GOAL_MAX_SCORE = 0.60   # bad goals should score BELOW this
GOOD_GOAL_MIN_SCORE = 0.70  # good goals should score ABOVE this


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["goals"]


def evaluate(goal_text):
    r = requests.post(f"{BASE}/api/v1/goals/evaluate", json={
        "employee_id": EMPLOYEE,
        "goal_text": goal_text,
        "quarter": QUARTER,
        "year": YEAR,
    })
    r.raise_for_status()
    return r.json()


def run():
    bad_goals = load("qa/fixtures/bad_goals_50.json")
    good_goals = load("qa/fixtures/good_goals_50.json")

    report = {
        "bad_goals": {"total": 0, "correctly_low": 0, "false_positives": [], "scores": []},
        "good_goals": {"total": 0, "correctly_high": 0, "false_negatives": [], "scores": []},
        "criteria_analysis": {
            "specific": {"bad_correct": 0, "bad_total": 0, "good_correct": 0, "good_total": 0},
            "measurable": {"bad_correct": 0, "bad_total": 0, "good_correct": 0, "good_total": 0},
            "achievable": {"bad_correct": 0, "bad_total": 0, "good_correct": 0, "good_total": 0},
            "relevant": {"bad_correct": 0, "bad_total": 0, "good_correct": 0, "good_total": 0},
            "timebound": {"bad_correct": 0, "bad_total": 0, "good_correct": 0, "good_total": 0},
        },
        "alignment_analysis": {"bad": {}, "good": {}},
        "goal_type_analysis": {"bad": {}, "good": {}},
    }

    # ── Evaluate BAD goals ──
    print("=== Оценка ПЛОХИХ целей (ожидаем score < {}) ===".format(BAD_GOAL_MAX_SCORE))
    for g in bad_goals:
        result = evaluate(g["text"])
        score = result["overall_score"]
        scores = result["scores"]
        report["bad_goals"]["total"] += 1
        report["bad_goals"]["scores"].append(score)

        if score < BAD_GOAL_MAX_SCORE:
            report["bad_goals"]["correctly_low"] += 1
        else:
            report["bad_goals"]["false_positives"].append({
                "id": g["id"],
                "text": g["text"],
                "expected_errors": g.get("errors", []),
                "got_score": score,
                "scores": scores,
                "alignment": result["alignment_level"],
                "goal_type": result["goal_type"],
                "recommendations": result["recommendations"],
            })
            print(f"  ❌ FP #{g['id']} score={score:.2f}: {g['text'][:70]}...")

        # Criteria analysis for bad goals
        for crit in ["specific", "measurable", "achievable", "relevant", "timebound"]:
            report["criteria_analysis"][crit]["bad_total"] += 1
            if scores[crit] < 0.7:
                report["criteria_analysis"][crit]["bad_correct"] += 1

        al = result["alignment_level"]
        report["alignment_analysis"]["bad"][al] = report["alignment_analysis"]["bad"].get(al, 0) + 1
        gt = result["goal_type"]
        report["goal_type_analysis"]["bad"][gt] = report["goal_type_analysis"]["bad"].get(gt, 0) + 1

    # ── Evaluate GOOD goals ──
    print("\n=== Оценка ХОРОШИХ целей (ожидаем score >= {}) ===".format(GOOD_GOAL_MIN_SCORE))
    for g in good_goals:
        result = evaluate(g["text"])
        score = result["overall_score"]
        scores = result["scores"]
        report["good_goals"]["total"] += 1
        report["good_goals"]["scores"].append(score)

        if score >= GOOD_GOAL_MIN_SCORE:
            report["good_goals"]["correctly_high"] += 1
        else:
            report["good_goals"]["false_negatives"].append({
                "id": g["id"],
                "text": g["text"],
                "got_score": score,
                "scores": scores,
                "alignment": result["alignment_level"],
                "goal_type": result["goal_type"],
                "recommendations": result["recommendations"],
            })
            print(f"  ❌ FN #{g['id']} score={score:.2f}: {g['text'][:70]}...")

        # Criteria analysis for good goals
        for crit in ["specific", "measurable", "achievable", "relevant", "timebound"]:
            report["criteria_analysis"][crit]["good_total"] += 1
            if scores[crit] >= 0.7:
                report["criteria_analysis"][crit]["good_correct"] += 1

        al = result["alignment_level"]
        report["alignment_analysis"]["good"][al] = report["alignment_analysis"]["good"].get(al, 0) + 1
        gt = result["goal_type"]
        report["goal_type_analysis"]["good"][gt] = report["goal_type_analysis"]["good"].get(gt, 0) + 1

    # ── Summary ──
    bad_acc = report["bad_goals"]["correctly_low"] / report["bad_goals"]["total"] * 100
    good_acc = report["good_goals"]["correctly_high"] / report["good_goals"]["total"] * 100
    overall_acc = (report["bad_goals"]["correctly_low"] + report["good_goals"]["correctly_high"]) / (report["bad_goals"]["total"] + report["good_goals"]["total"]) * 100
    bad_avg = sum(report["bad_goals"]["scores"]) / len(report["bad_goals"]["scores"])
    good_avg = sum(report["good_goals"]["scores"]) / len(report["good_goals"]["scores"])

    print("\n" + "=" * 70)
    print("ИТОГОВЫЙ ОТЧЁТ ТОЧНОСТИ ОЦЕНКИ ЦЕЛЕЙ")
    print("=" * 70)
    print(f"Плохие цели:   {report['bad_goals']['correctly_low']}/{report['bad_goals']['total']} правильно определены как слабые ({bad_acc:.1f}%)")
    print(f"  Средний score: {bad_avg:.3f}  |  False Positives: {len(report['bad_goals']['false_positives'])}")
    print(f"Хорошие цели:  {report['good_goals']['correctly_high']}/{report['good_goals']['total']} правильно определены как хорошие ({good_acc:.1f}%)")
    print(f"  Средний score: {good_avg:.3f}  |  False Negatives: {len(report['good_goals']['false_negatives'])}")
    print(f"Общая точность: {overall_acc:.1f}%")
    print(f"Разделение (gap): {good_avg - bad_avg:.3f}  (чем больше — тем лучше)")

    print("\n── Точность по критериям ──")
    for crit, data in report["criteria_analysis"].items():
        bad_pct = data["bad_correct"] / data["bad_total"] * 100 if data["bad_total"] else 0
        good_pct = data["good_correct"] / data["good_total"] * 100 if data["good_total"] else 0
        flag = "⚠️" if bad_pct < 70 or good_pct < 70 else "✅"
        print(f"  {flag} {crit:12s}: плохие<0.7: {data['bad_correct']}/{data['bad_total']} ({bad_pct:.0f}%)  |  хорошие>=0.7: {data['good_correct']}/{data['good_total']} ({good_pct:.0f}%)")

    print("\n── Alignment distribution ──")
    print(f"  Bad:  {report['alignment_analysis']['bad']}")
    print(f"  Good: {report['alignment_analysis']['good']}")

    print("\n── Goal type distribution ──")
    print(f"  Bad:  {report['goal_type_analysis']['bad']}")
    print(f"  Good: {report['goal_type_analysis']['good']}")

    if report["bad_goals"]["false_positives"]:
        print(f"\n── False Positives ({len(report['bad_goals']['false_positives'])}) — плохие цели с высоким score ──")
        for fp in report["bad_goals"]["false_positives"]:
            print(f"  #{fp['id']} score={fp['got_score']:.2f} | {fp['text'][:80]}")
            print(f"     scores: S={fp['scores']['specific']:.2f} M={fp['scores']['measurable']:.2f} A={fp['scores']['achievable']:.2f} R={fp['scores']['relevant']:.2f} T={fp['scores']['timebound']:.2f}")
            print(f"     errors: {', '.join(fp['expected_errors'][:3])}")

    if report["good_goals"]["false_negatives"]:
        print(f"\n── False Negatives ({len(report['good_goals']['false_negatives'])}) — хорошие цели с низким score ──")
        for fn in report["good_goals"]["false_negatives"]:
            print(f"  #{fn['id']} score={fn['got_score']:.2f} | {fn['text'][:80]}")
            print(f"     scores: S={fn['scores']['specific']:.2f} M={fn['scores']['measurable']:.2f} A={fn['scores']['achievable']:.2f} R={fn['scores']['relevant']:.2f} T={fn['scores']['timebound']:.2f}")

    # Save JSON report
    with open("qa/diagnostic_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\nJSON-отчёт сохранён: qa/diagnostic_report.json")


if __name__ == "__main__":
    run()
