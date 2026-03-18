# GoalCraft AI — Backend

> Полная документация проекта: [../README.md](../README.md)

## Быстрый запуск

```bash
# Установить зависимости (из корня проекта)
pip install -r ../requirements.txt

# (Опционально) LLM через OpenAI
# Windows:  $env:OPENAI_API_KEY = "sk-proj-..."
# Linux:    export OPENAI_API_KEY="sk-proj-..."

# Запуск
uvicorn app.main:app --host 0.0.0.0 --port 8899

# Swagger UI
# http://localhost:8899/docs
```

## Структура

```
app/
  api/routes.py          # 16 REST-эндпоинтов
  core/config.py         # Конфигурация (env vars)
  container.py           # DI-контейнер
  main.py                # FastAPI entry point
  models/schemas.py      # Pydantic-модели (Goal §2.1, Document §2.2, Notifications)
  services/
    engine.py            # GoalEngine — бизнес-логика (950+ строк)
    rules.py             # SMART-правила (300+ строк, детерминированные)
    llm.py               # LLM-сервис (GPT-4o-mini, graceful degradation)
  storage/
    memory.py            # In-memory хранилище (8 отделов, 6 сотрудников, 10 ВНД, 18 целей)
    postgres.py          # PostgreSQL production store (13 таблиц)
  vector/
    memory_vector.py     # In-memory векторный поиск
    qdrant_vector.py     # Qdrant vector store
```

## Тесты

```bash
python qa/run_api_contract_tests.py    # 14+ контрактных тестов
python qa/quick_test.py                # 16 эндпоинтов
python qa/run_diagnostic_50.py         # 100 целей (50 bad + 50 good)
```

## Docker

```bash
cp .env.example .env   # заполнить значения
docker compose up -d
```

## Эндпоинты (16)

| Метод | Путь | Назначение |
|-------|------|----------|
| GET | /health | Статус системы |
| POST | /api/v1/goals/evaluate | SMART-оценка цели |
| POST | /api/v1/goals/rewrite | Переформулировка цели |
| POST | /api/v1/goals/generate | Генерация 3–5 целей |
| POST | /api/v1/goals/evaluate-batch | Пакетная оценка |
| POST | /api/v1/goals/cascade | Каскадирование от руководителя |
| GET | /api/v1/dashboard/overview | Дашборд всех подразделений |
| GET | /api/v1/dashboard/{id} | Детали подразделения |
| GET | /api/v1/dashboard/{id}/maturity | Индекс зрелости |
| POST | /api/v1/documents/ingest | Загрузка ВНД / стратегий |
| GET | /api/v1/employees/{id}/context | Контекст сотрудника |
| GET | /api/v1/goals/{id}/history | История изменений цели (F-15) |
| GET | /api/v1/notifications | **Уведомления / Alert Manager** |
| GET | /api/v1/data/stats | Статистика загруженных данных (§4.2) |
| GET | /api/v1/departments | Справочник подразделений |
| GET | /api/v1/employees | Справочник сотрудников |

## Важно
В текущем artifact проект по умолчанию работает в demo-safe режиме, чтобы запускаться без внешней инфраструктуры и без падений в среде, где пока нет драйверов/клиентов. Структура уже подготовлена для следующего шага: подключение реального PostgreSQL-репозитория и Qdrant retrieval.
