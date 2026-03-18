# GoalCraft AI — единый пакет проекта

> **AI-платформа управления целями персонала**  
> SMART-оценка • RAG-поиск • LLM-генерация • Аналитический дашборд

## 📦 Содержимое

| Директория | Описание |
|-----------|----------|
| `backend_project/` | Модульный backend (FastAPI + 17 эндпоинтов + 989-строчный GoalEngine) |
| `backend_project/frontend/` | React 18 + TypeScript + Vite (5 страниц, 7 компонентов, Recharts) |
| `backend_project/qa/` | 7 тестовых сьютов (251 тест, 99.6% pass rate) |
| `requirements.txt` | Python-зависимости |
| `.env.example` | Переменные окружения |
| `backend_project/docker-compose.yml` | Docker Compose: api + PostgreSQL 17 + Qdrant |

## 🚀 Быстрый старт (Demo — без Docker)

```bash
# 1. Установите зависимости
pip install -r requirements.txt

# 2. Запустите бэкенд
cd backend_project
uvicorn app.main:app --host 0.0.0.0 --port 8899

# 3. Swagger UI
# http://localhost:8899/docs

# 4. (Опционально) Фронтенд
cd frontend && npm install && npm run dev
# http://localhost:5173
```

## 🐳 Production (Docker Compose)

```bash
cd backend_project
cp .env.example .env    # настройте OPENAI_API_KEY
docker compose up --build -d
```

## ✅ Тесты

```bash
cd backend_project
python qa/run_api_contract_tests.py     # 15/15 контрактных тестов
python qa/run_comprehensive_tests.py    # 61/61 комплексных тестов
python qa/run_diagnostic_50.py          # 99/100 accuracy (99%)
python qa/smoke_endpoints.py            # 17/17 endpoints
python qa/run_frontend_tests.py         # 34/34 frontend тестов
```

## 📖 Документация

Подробная презентация проекта с архитектурой, алгоритмами оценки, RAG-системой и метриками — в `backend_project/README.md`.

## 📊 Ключевые метрики

- **8,275** строк кода (48 файлов)
- **17** REST API эндпоинтов, **30** Pydantic-моделей
- **13** таблиц БД (§4.2), **47,857** синтетических записей
- **251** тест, **99%** accuracy SMART-скоринга
- **Dual-mode**: demo (zero-config) / production (PostgreSQL + Qdrant + GPT-4o-mini)
