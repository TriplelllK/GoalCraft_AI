# Final Run Guide — HR Goal AI

## Что внутри проекта
- backend FastAPI
- frontend React + Vite
- тестовые фикстуры для API
- ручной UAT-чеклист
- автоматический test runner

## Быстрый запуск всего стека
```bash
docker compose up --build
```

После запуска:
- Backend docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:5173`

## Быстрый запуск только backend
```bash
export STORAGE_BACKEND=memory
export VECTOR_BACKEND=memory
uvicorn app.main:app --reload
```

## Запуск автоматических тестов
```bash
python qa/run_api_contract_tests.py
```

## Фикстуры для прогона
- `qa/fixtures/evaluate_cases.json`
- `qa/fixtures/generate_cases.json`
- `qa/fixtures/batch_cases.json`
- `qa/fixtures/ingest_documents.json`

## Ручная проверка
Использовать:
- `qa/UAT_CHECKLIST.md`

## Уже проверено в этой сборке
- API contract tests: `7/7 passed`
- test report: `qa/test_report.md`, `qa/test_report.json`
