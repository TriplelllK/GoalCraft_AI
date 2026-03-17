from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings


app = FastAPI(title=settings.app_title, version=settings.app_version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


if __name__ == "__main__":
    from fastapi.testclient import TestClient

    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert client.post(
        "/api/v1/goals/evaluate",
        json={"employee_id": "emp_1", "goal_text": "Улучшить процесс обучения сотрудников", "quarter": "Q2", "year": 2026},
    ).status_code == 200
    assert client.post(
        "/api/v1/goals/generate",
        json={"employee_id": "emp_1", "quarter": "Q2", "year": 2026, "count": 3},
    ).status_code == 200
    print("Self-check passed. Start with: uvicorn app.main:app --reload")
