from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
FIXTURES = ROOT / "qa" / "fixtures"


def load_json(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class InProcessClient:
    def __init__(self) -> None:
        from fastapi.testclient import TestClient
        from app.main import app

        self.client = TestClient(app)

    def get(self, path: str) -> tuple[int, Any]:
        response = self.client.get(path)
        return response.status_code, response.json()

    def post(self, path: str, payload: Any) -> tuple[int, Any]:
        response = self.client.post(path, json=payload)
        return response.status_code, response.json()


class LiveHttpClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, payload: Any | None = None) -> tuple[int, Any]:
        data = None
        headers = {"Content-Type": "application/json"}
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(self.base_url + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                body = resp.read().decode("utf-8")
                return resp.status, json.loads(body)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8")
            return exc.code, json.loads(body) if body else {"detail": exc.reason}

    def get(self, path: str) -> tuple[int, Any]:
        return self._request("GET", path)

    def post(self, path: str, payload: Any) -> tuple[int, Any]:
        return self._request("POST", path, payload)


class CheckFailure(AssertionError):
    pass


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


class TestRunner:
    def __init__(self, client: Any) -> None:
        self.client = client
        self.results: list[dict[str, Any]] = []

    def record(self, name: str, ok: bool, details: str, payload_preview: Any | None = None) -> None:
        self.results.append(
            {
                "name": name,
                "status": "passed" if ok else "failed",
                "details": details,
                "payload_preview": payload_preview,
            }
        )

    def run_case(self, name: str, fn) -> None:
        try:
            payload_preview = fn()
            self.record(name, True, "ok", payload_preview)
        except Exception as exc:  # noqa: BLE001
            self.record(name, False, str(exc))

    def check_health(self) -> Any:
        status, payload = self.client.get("/health")
        assert_true(status == 200, f"/health returned {status}")
        assert_true(payload["status"] == "ok", "health status must be ok")
        assert_true(payload["indexed_documents"] >= 5, "expected seeded documents")
        return payload

    def check_employee_context(self) -> Any:
        status, payload = self.client.get("/api/v1/employees/emp_1/context?quarter=Q2&year=2026")
        assert_true(status == 200, f"employee context returned {status}")
        assert_true(payload["employee"]["id"] == "emp_1", "wrong employee id")
        assert_true(payload["department"]["id"] == "dep_hr", "wrong department")
        assert_true(len(payload["active_goals"]) >= 2, "seeded employee should have at least 2 active goals")
        # §4.2 extended context fields
        assert_true("projects" in payload, "projects field missing from employee context")
        assert_true("department_kpis" in payload, "department_kpis field missing from employee context")
        assert_true("goal_history_stats" in payload, "goal_history_stats field missing from employee context")
        return payload

    def check_ingest(self) -> Any:
        fixture = load_json("ingest_documents.json")
        status, payload = self.client.post("/api/v1/documents/ingest", fixture)
        assert_true(status == 200, f"ingest returned {status}")
        assert_true(payload["indexed_documents"] == len(fixture["documents"]), "wrong indexed_documents count")
        assert_true(payload["indexed_chunks"] >= 7, "expected index to grow after ingest")
        return payload

    def check_evaluate_cases(self) -> Any:
        previews = []
        for case in load_json("evaluate_cases.json"):
            status, payload = self.client.post("/api/v1/goals/evaluate", case["request"])
            assert_true(status == 200, f"{case['name']}: status {status}")
            exp = case["expect"]
            if "overall_score_min" in exp:
                assert_true(payload["overall_score"] >= exp["overall_score_min"], f"{case['name']}: overall_score too low")
            if "overall_score_max" in exp:
                assert_true(payload["overall_score"] <= exp["overall_score_max"], f"{case['name']}: overall_score too high")
            if "alignment_level" in exp:
                assert_true(payload["alignment_level"] == exp["alignment_level"], f"{case['name']}: wrong alignment")
            if "goal_type" in exp:
                assert_true(payload["goal_type"] == exp["goal_type"], f"{case['name']}: wrong goal_type")
            for fragment in exp.get("recommendations_contains", []):
                assert_true(any(fragment in item for item in payload["recommendations"]), f"{case['name']}: missing recommendation fragment '{fragment}'")
            for fragment in exp.get("rewrite_contains", []):
                assert_true(fragment in payload["rewrite"], f"{case['name']}: rewrite missing '{fragment}'")
            if "rewrite_min_length" in exp:
                assert_true(len(payload["rewrite"]) >= exp["rewrite_min_length"], f"{case['name']}: rewrite too short ({len(payload['rewrite'])} < {exp['rewrite_min_length']})")
            if exp.get("source_required"):
                assert_true(payload.get("source") is not None, f"{case['name']}: source is missing")
            allowed_doc_types = exp.get("source_doc_types")
            if allowed_doc_types:
                assert_true(payload["source"]["doc_type"] in allowed_doc_types, f"{case['name']}: unexpected source doc_type")
            previews.append({"name": case["name"], "overall_score": payload["overall_score"], "alignment": payload["alignment_level"]})
        return previews

    def check_generate_cases(self) -> Any:
        previews = []
        for case in load_json("generate_cases.json"):
            status, payload = self.client.post("/api/v1/goals/generate", case["request"])
            assert_true(status == 200, f"{case['name']}: status {status}")
            exp = case["expect"]
            assert_true(len(payload) == exp["count"], f"{case['name']}: wrong generated count")
            for idx, item in enumerate(payload):
                assert_true(item["score"] >= exp["score_min"], f"{case['name']}: item {idx} score too low")
                assert_true(item["alignment_level"] in exp["allowed_alignment_levels"], f"{case['name']}: item {idx} invalid alignment")
                assert_true(item["goal_type"] in exp["allowed_goal_types"], f"{case['name']}: item {idx} invalid goal type")
                if exp.get("source_required"):
                    assert_true(item.get("source") is not None, f"{case['name']}: item {idx} has no source")
            previews.append({"name": case["name"], "count": len(payload), "sample_titles": [item["title"] for item in payload[:2]]})
        return previews

    def check_batch_cases(self) -> Any:
        previews = []
        for case in load_json("batch_cases.json"):
            status, payload = self.client.post("/api/v1/goals/evaluate-batch", case["request"])
            assert_true(status == 200, f"{case['name']}: status {status}")
            exp = case["expect"]
            assert_true(payload["goal_count"] == exp["goal_count"], f"{case['name']}: wrong goal_count")
            if "average_smart_index_min" in exp:
                assert_true(payload["average_smart_index"] >= exp["average_smart_index_min"], f"{case['name']}: average_smart_index too low")
            if "average_smart_index_max" in exp:
                assert_true(payload["average_smart_index"] <= exp["average_smart_index_max"], f"{case['name']}: average_smart_index too high")
            if "strategic_goal_share_min" in exp:
                assert_true(payload["strategic_goal_share"] >= exp["strategic_goal_share_min"], f"{case['name']}: strategic_goal_share too low")
            if "total_weight" in exp:
                assert_true(abs(float(payload["total_weight"]) - float(exp["total_weight"])) < 1e-6, f"{case['name']}: wrong total_weight")
            assert_true(payload["duplicates_found"] == exp["duplicates_found"], f"{case['name']}: wrong duplicates_found")
            for fragment in exp.get("alerts_contains", []):
                assert_true(any(fragment in item for item in payload["alerts"]), f"{case['name']}: missing alert '{fragment}'")
            previews.append({"name": case["name"], "average_smart_index": payload["average_smart_index"], "alerts": payload["alerts"]})
        return previews

    def check_dashboard(self) -> Any:
        status, overview = self.client.get("/api/v1/dashboard/overview?quarter=Q2&year=2026")
        assert_true(status == 200, f"overview returned {status}")
        assert_true(overview["total_departments"] == 8, "expected 8 departments")
        assert_true(overview["total_goals_evaluated"] >= 2, "expected at least 2 seeded goals")
        # F-22: check maturity fields are present
        for dept in overview.get("departments", []):
            assert_true("maturity_index" in dept, "maturity_index missing from department snapshot")
            assert_true("maturity_level" in dept, "maturity_level missing from department snapshot")
        status, department = self.client.get("/api/v1/dashboard/departments/dep_hr?quarter=Q2&year=2026")
        assert_true(status == 200, f"department snapshot returned {status}")
        assert_true(department["department_id"] == "dep_hr", "wrong department id")
        assert_true(department["avg_smart_score"] >= 0.7, "HR department avg score too low")
        assert_true(department["maturity_index"] > 0, "maturity_index should be positive")
        return {"overview": overview, "department": department}

    def check_achievability(self) -> Any:
        """F-20: Check that evaluate response includes achievability data."""
        status, payload = self.client.post("/api/v1/goals/evaluate", {
            "employee_id": "emp_1",
            "goal_text": "До 30.06 сократить средний срок согласования HR-заявок с 5 до 3 рабочих дней за счет цифровизации маршрута согласования",
            "quarter": "Q2",
            "year": 2026,
        })
        assert_true(status == 200, f"evaluate returned {status}")
        assert_true("achievability" in payload, "achievability field is missing")
        ach = payload["achievability"]
        assert_true("is_achievable" in ach, "is_achievable missing")
        assert_true("confidence" in ach, "confidence missing")
        assert_true("similar_goals_found" in ach, "similar_goals_found missing")
        assert_true(ach["similar_goals_found"] >= 1, "should find similar historical goals")
        return {"achievability": ach, "overall_score": payload["overall_score"]}

    def check_cascade_cases(self) -> Any:
        """F-14: Check cascade goal generation from manager."""
        previews = []
        for case in load_json("cascade_cases.json"):
            status, payload = self.client.post("/api/v1/goals/cascade", case["request"])
            assert_true(status == 200, f"{case['name']}: status {status}")
            exp = case["expect"]
            assert_true(len(payload["subordinates"]) == exp["subordinate_count"], f"{case['name']}: wrong subordinate count")
            assert_true(len(payload.get("manager_goals", [])) >= exp["manager_goals_min"], f"{case['name']}: expected manager goals")
            for sub in payload["subordinates"]:
                assert_true(len(sub["goals"]) == exp["goals_per_subordinate"], f"{case['name']}: wrong goals for {sub['employee_name']}")
                for g in sub["goals"]:
                    assert_true(exp["rationale_contains"] in g["rationale"], f"{case['name']}: rationale missing cascade ref")
            previews.append({
                "name": case["name"],
                "manager_goals": len(payload.get("manager_goals", [])),
                "subordinates": [{"name": s["employee_name"], "goals": len(s["goals"])} for s in payload["subordinates"]],
                "total_generated": payload["total_generated"],
            })
        return previews

    def check_maturity_cases(self) -> Any:
        """F-22: Check maturity report endpoint."""
        previews = []
        for case in load_json("maturity_cases.json"):
            req = case["request"]
            status, payload = self.client.get(f"/api/v1/dashboard/departments/{req['department_id']}/maturity?quarter={req['quarter']}&year={req['year']}")
            assert_true(status == 200, f"{case['name']}: status {status}")
            exp = case["expect"]
            assert_true(payload["maturity_index"] >= exp["maturity_index_min"], f"{case['name']}: maturity_index too low")
            assert_true(payload["total_employees"] >= exp["total_employees_min"], f"{case['name']}: not enough employees")
            assert_true(payload["employees_with_goals"] >= exp["employees_with_goals_min"], f"{case['name']}: not enough employees with goals")
            assert_true(payload["total_goals"] >= exp["total_goals_min"], f"{case['name']}: not enough goals")
            if exp.get("has_smart_distribution"):
                assert_true("smart_distribution" in payload, f"{case['name']}: smart_distribution missing")
            if exp.get("has_goal_type_distribution"):
                assert_true("goal_type_distribution" in payload, f"{case['name']}: goal_type_distribution missing")
            if exp.get("has_alignment_distribution"):
                assert_true("alignment_distribution" in payload, f"{case['name']}: alignment_distribution missing")
            if exp.get("has_weakest_criteria"):
                assert_true(len(payload.get("weakest_criteria", [])) > 0, f"{case['name']}: weakest_criteria empty")
            if exp.get("has_recommendations"):
                assert_true(len(payload.get("top_recommendations", [])) > 0, f"{case['name']}: recommendations empty")
            previews.append({
                "name": case["name"],
                "maturity_index": payload["maturity_index"],
                "maturity_level": payload["maturity_level"],
                "total_goals": payload["total_goals"],
                "recommendations": payload["top_recommendations"][:2],
            })
        return previews

    def check_goal_history(self) -> Any:
        """F-15: Check goal history/versioning endpoint."""
        status, payload = self.client.get("/api/v1/goals/goal_hr_001/history")
        assert_true(status == 200, f"goal history returned {status}")
        assert_true(payload["goal_id"] == "goal_hr_001", "wrong goal_id")
        assert_true("events" in payload, "events list missing")
        assert_true("reviews" in payload, "reviews list missing")
        assert_true("total_events" in payload, "total_events missing")
        assert_true("total_reviews" in payload, "total_reviews missing")
        return payload

    def check_data_stats(self) -> Any:
        """§4.2: Check data stats endpoint for dump verification."""
        status, payload = self.client.get("/api/v1/data/stats")
        assert_true(status == 200, f"data stats returned {status}")
        assert_true(payload["departments"] == 8, "expected 8 departments")
        assert_true(payload["employees"] >= 6, "expected at least 6 employees")
        assert_true(payload["goals"] >= 18, "expected at least 18 goals")
        assert_true("has_dump_data" in payload, "has_dump_data field missing")
        return payload

    def check_list_departments(self) -> Any:
        """Reference: List departments for UI dropdowns."""
        status, payload = self.client.get("/api/v1/departments")
        assert_true(status == 200, f"list departments returned {status}")
        assert_true(isinstance(payload, list), "expected list of departments")
        assert_true(len(payload) == 8, f"expected 8 departments, got {len(payload)}")
        first = payload[0]
        assert_true("id" in first, "department id missing")
        assert_true("name" in first, "department name missing")
        assert_true("code" in first, "department code missing")
        return payload[:3]

    def check_list_employees(self) -> Any:
        """Reference: List employees for UI dropdowns."""
        status, payload = self.client.get("/api/v1/employees")
        assert_true(status == 200, f"list employees returned {status}")
        assert_true(isinstance(payload, list), "expected list of employees")
        assert_true(len(payload) >= 6, f"expected at least 6 employees, got {len(payload)}")
        first = payload[0]
        assert_true("id" in first, "employee id missing")
        assert_true("full_name" in first, "full_name missing")
        assert_true("department_name" in first, "department_name missing")
        assert_true("position_name" in first, "position_name missing")
        return payload[:3]

    def check_notifications(self) -> Any:
        """Alert Manager: Notifications endpoint."""
        status, payload = self.client.get("/api/v1/notifications?quarter=Q2&year=2026")
        assert_true(status == 200, f"notifications returned {status}")
        assert_true("total" in payload, "total missing")
        assert_true("critical" in payload, "critical count missing")
        assert_true("warnings" in payload, "warnings count missing")
        assert_true("items" in payload, "items list missing")
        assert_true(isinstance(payload["items"], list), "items should be a list")
        assert_true(payload["total"] >= 0, "total must be non-negative")
        if payload["items"]:
            first = payload["items"][0]
            assert_true("id" in first, "notification id missing")
            assert_true("severity" in first, "severity missing")
            assert_true(first["severity"] in ("critical", "warning", "info"), f"unknown severity: {first['severity']}")
            assert_true("title" in first, "notification title missing")
            assert_true("message" in first, "notification message missing")
        return {"total": payload["total"], "critical": payload["critical"], "warnings": payload["warnings"]}

    def run_all(self) -> dict[str, Any]:
        self.run_case("health", self.check_health)
        self.run_case("employee_context", self.check_employee_context)
        self.run_case("documents_ingest", self.check_ingest)
        self.run_case("evaluate_cases", self.check_evaluate_cases)
        self.run_case("generate_cases", self.check_generate_cases)
        self.run_case("batch_cases", self.check_batch_cases)
        self.run_case("dashboard", self.check_dashboard)
        self.run_case("achievability_check", self.check_achievability)
        self.run_case("cascade_goals", self.check_cascade_cases)
        self.run_case("maturity_report", self.check_maturity_cases)
        self.run_case("goal_history", self.check_goal_history)
        self.run_case("data_stats", self.check_data_stats)
        self.run_case("list_departments", self.check_list_departments)
        self.run_case("list_employees", self.check_list_employees)
        self.run_case("notifications", self.check_notifications)
        passed = sum(1 for item in self.results if item["status"] == "passed")
        failed = len(self.results) - passed
        return {
            "summary": {
                "passed": passed,
                "failed": failed,
                "total": len(self.results),
            },
            "results": self.results,
        }


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# API contract test report", ""]
    s = report["summary"]
    lines.append(f"Passed: **{s['passed']}** / {s['total']}")
    lines.append(f"Failed: **{s['failed']}**")
    lines.append("")
    for item in report["results"]:
        icon = "✅" if item["status"] == "passed" else "❌"
        lines.append(f"## {icon} {item['name']}")
        lines.append(item["details"])
        if item.get("payload_preview") is not None:
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(item["payload_preview"], ensure_ascii=False, indent=2))
            lines.append("```")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run API contract tests for HR Goal AI backend")
    parser.add_argument("--live", help="Base URL for live API, e.g. http://localhost:8000")
    parser.add_argument("--json-out", default=str(ROOT / "qa" / "test_report.json"))
    parser.add_argument("--md-out", default=str(ROOT / "qa" / "test_report.md"))
    args = parser.parse_args()

    client = LiveHttpClient(args.live) if args.live else InProcessClient()
    runner = TestRunner(client)
    report = runner.run_all()

    Path(args.json_out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.md_out).write_text(render_markdown(report), encoding="utf-8")

    summary = report["summary"]
    print(json.dumps(summary, ensure_ascii=False))
    if summary["failed"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
