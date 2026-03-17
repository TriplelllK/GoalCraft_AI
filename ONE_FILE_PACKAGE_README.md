# GoalCraft AI — единый пакет проекта

Содержимое:
- `backend_project/` — модульный backend-проект (FastAPI + Postgres/Qdrant adapters)
- `backend_project/frontend/` — React/Vite frontend
- `backend_project/qa/` — тестовые фикстуры, API contract tests, UAT checklist, run guide
- `requirements.txt` — Python зависимости
- `.env.example` — пример переменных окружения
- `goalcraft_demo_day_deck.pptx` — презентация Demo Day
- `Hrhackathon_1.docx` — исходное ТЗ

Быстрый старт:
1. Перейдите в `backend_project/`
2. Поднимите стек: `docker compose up --build`
3. Или запустите backend локально: `uvicorn app.main:app --reload`
4. Прогон тестов: `python qa/run_api_contract_tests.py`

Примечание:
Текущий пакет объединяет ранее созданные артефакты в один архив для удобной передачи и запуска.
