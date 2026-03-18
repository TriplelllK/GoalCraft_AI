# 🎯 GoalCraft AI — HR Performance Management Platform

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react" alt="React">
  <img src="https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai" alt="OpenAI">
  <img src="https://img.shields.io/badge/Accuracy-100%25-brightgreen" alt="Accuracy">
  <img src="https://img.shields.io/badge/Tests-10%2F10-brightgreen" alt="Tests">
</p>

**GoalCraft AI** — интеллектуальная платформа для управления целями сотрудников (Performance Management), которая автоматически оценивает, генерирует и улучшает рабочие цели по комбинированной методологии **SMART + OKR** с использованием гибридного подхода: детерминированные правила + LLM (GPT-4o-mini).

> 🏆 Проект создан в рамках хакатона по теме «Внедрение ИИ в HR-процессы»

---

## 📋 Соответствие ТЗ

### Компонент A: AI-оценка качества и релевантности целей (§3.1)

| Требование ТЗ | Реализация | Статус |
|----------------|-----------|--------|
| SMART-оценка по 5 критериям (S/M/A/R/T) | `rules.py`: 40+ глаголов, 60+ объектов, regex-паттерны | ✅ |
| Итоговый индекс (Float 0.0–1.0) | `overall_score` — среднее 5 SMART-критериев | ✅ |
| Рекомендации (Text список) | Контекстные рекомендации по каждому слабому критерию | ✅ |
| Переформулировка AI | LLM-переписывание + rule-based fallback | ✅ |
| Методология SMART + альтернативные | SMART + OKR (Objectives & Key Results) комбинированная | ✅ |

### Компонент B: AI-генерация целей (§3.2)

| Функция (ID) | Описание | Статус |
|--------------|----------|--------|
| **F-09** | Генерация целей по должности, подразделению и ВНД | ✅ |
| **F-10** | Привязка к ВНД / стратегическому документу (источник + цитата) | ✅ |
| **F-11** | Настройка фокус-направления (приоритеты квартала) | ✅ |
| **F-12** | Генерация в SMART-формате, автоматическая переформулировка при score < 0.7 | ✅ |
| **F-13** | Выбор целей из предложенного набора (UI-интерфейс) | ✅ |
| **F-14** | Каскадирование целей от руководителя к подчинённым | ✅ |
| **F-15** | Версионирование: история изменений целей (events + reviews) | ✅ |
| **F-16** | Проверка количества целей (< 3 или > 5 — предупреждение) | ✅ |
| **F-17** | Стратегическая связка: strategic / functional / operational + источник | ✅ |
| **F-18** | Контроль веса целей (суммарный вес ≠ 100% → предупреждение) | ✅ |
| **F-19** | Тип цели: activity-based / output-based / impact-based | ✅ |
| **F-20** | Достижимость на основе исторических данных (аналогичные роли/подразделения) | ✅ |
| **F-21** | Проверка дублирования (в batch + при генерации per §3.2.2 step 4) | ✅ |
| **F-22** | Индекс зрелости подразделения (maturity_index + maturity_level) | ✅ |

### Логика генерации (§3.2.2)

| Шаг | Описание | Статус |
|-----|----------|--------|
| 1. Retrieval (RAG) | Векторный поиск по ВНД и стратегиям | ✅ |
| 2. Контекстуализация | Должность + подразделение + цели руководителя | ✅ |
| 3. Генерация (LLM) | GPT-4o-mini + автоматическая переформулировка при < 0.7 | ✅ |
| 4. Верификация | Проверка дублирования с существующими целями сотрудника | ✅ |

### MVP (§8) — Все обязательные функции реализованы

| MVP-функция | Обязательно | Статус |
|-------------|-------------|--------|
| SMART-оценка одной цели через API | ✅ Да | ✅ |
| Переформулировка слабой цели | ✅ Да | ✅ |
| Генерация 3–5 целей по должности | ✅ Да | ✅ |
| Привязка к источнику ВНД | ✅ Да | ✅ |
| Пакетная оценка за квартал | ✅ Да | ✅ |
| Дашборд качества по подразделениям | ✅ Да | ✅ |
| Каскадирование целей от руководителя | ⭕ Опционально | ✅ |

### Модель данных (§2.1, §2.2)

**Goal** (соответствие ТЗ §2.1):
```
id, employee_id, department_id, position, title, goal_text, metric, deadline,
weight, status, quarter, year, reviewer_comment, created_at, updated_at
```

**Document** (соответствие ТЗ §2.2):
```
doc_id, doc_type (strategy/vnd/kpi/policy/manager_goal),
title, content, valid_from, valid_to, department_scope, keywords, version
```

### Данные для хакатона (§4.2)

Система готова принять `.sql` дамп от организаторов (PostgreSQL 17+ custom format).
Все 13 таблиц из §4.2 поддерживаются:

| Таблица | Записей (ТЗ) | Описание |
|---------|-------------|----------|
| departments | 8 | Подразделения |
| positions | 25 | Должности и грейды |
| employees | 450 | Сотрудники с иерархией |
| documents | 160 | ВНД, стратегии, KPI-фреймворки |
| goals | 9 000 | Цели сотрудников за все периоды |
| projects | 34 | Проекты компании |
| systems | 10 | ИТ-системы |
| project_systems | 65 | Связь проект↔система |
| employee_projects | 886 | Связь сотрудник↔проект (роль, %) |
| goal_events | 30 789 | Журнал изменений целей (F-15) |
| goal_reviews | 4 305 | Рецензии руководителей на цели |
| kpi_catalog | 13 | Каталог KPI (название, единица) |
| kpi_timeseries | 2 112 | Временные ряды KPI по подразделениям |

**Загрузка дампа:**
```bash
# Вариант 1: Docker (автоматически при первом запуске)
cp hackathon_dump.sql backend_project/data/
docker compose up --build

# Вариант 2: psql
psql -U postgres -d hr_goal_ai -f hackathon_dump.sql

# Вариант 3: Python-скрипт
python scripts/load_dump.py hackathon_dump.sql

# Проверка загрузки
python scripts/load_dump.py --verify-only
# Или через API: GET /api/v1/data/stats
```

### Технический стек (§4.1)

| Требование ТЗ | Наша реализация | Обоснование |
|----------------|----------------|-------------|
| PostgreSQL | ✅ PostgreSQL 17 | Production-ready через Docker Compose |
| ChromaDB / Qdrant / FAISS | ✅ Qdrant | Qdrant — лучший выбор для production: REST API + Docker |
| Python, HuggingFace | ✅ Python + OpenAI GPT-4o-mini | GPT-4o-mini: выше качество генерации, чем HuggingFace локальные модели |
| sentence-transformers / OpenAI embeddings | ✅ TF-IDF-like (demo) / Qdrant (prod) | Demo: встроенный векторный поиск. Prod: Qdrant с embeddings |
| FastAPI / Flask | ✅ FastAPI | Async, автодокументация (Swagger), type-safe |
| React / Vue.js | ✅ React 18 + TypeScript + Vite | SPA с 3 страницами: Dashboard, Evaluate, Generate |

---

## 🏗️ Архитектура

### Общая схема (§5)

```
┌─────────────────────────────────────────────────────────────────┐
│                     React SPA (Vite + TS)                       │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │Dashboard │  │  Evaluate    │  │  Generate     │              │
│  │  Page    │  │   Page       │  │   Page        │              │
│  └────┬─────┘  └──────┬───────┘  └──────┬────────┘              │
│       └───────────────┼──────────────────┘                      │
│                       │ HTTP REST API                           │
└───────────────────────┼─────────────────────────────────────────┘
                        │
┌───────────────────────┼─────────────────────────────────────────┐
│                 FastAPI Backend                                  │
│  ┌────────────────────┴──────────────────────────────────────┐  │
│  │                   API Router (routes.py)                   │  │
│  │  /health  /evaluate  /generate  /rewrite  /batch          │  │
│  │  /cascade /dashboard /maturity /ingest /context            │  │
│  │  /goals/{id}/history  /data/stats                         │  │
│  └────────────────────┬──────────────────────────────────────┘  │
│  ┌────────────────────┴──────────────────────────────────────┐  │
│  │              GoalEngine (engine.py, 845+ lines)           │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │  │
│  │  │ SMART Rules  │  │  LLM Service │  │  RAG / Vector  │  │  │
│  │  │ (rules.py)   │  │  (llm.py)    │  │  Search        │  │  │
│  │  │ Deterministic│  │  GPT-4o-mini │  │  ВНД/Strategy  │  │  │
│  │  └──────────────┘  └──────────────┘  └────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌────────────────────┐  ┌─────────────────────────────────┐   │
│  │   Storage Layer    │  │      Vector Store Layer          │   │
│  │  Memory / Postgres │  │    Memory / Qdrant              │   │
│  └────────────────────┘  └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Потоки данных (§5.1)

| Поток | Описание |
|-------|----------|
| **Оценка** | Цель → Quality Evaluator → SMART-оценка + рекомендации + OKR → UI |
| **Генерация** | Профиль сотрудника → RAG-поиск ВНД → LLM-генерация → SMART-проверка → дедупликация → Список целей |
| **Аналитика** | Все оценки → Агрегация → Дашборд по подразделениям и кварталам |

### Гибридный подход (Rule-based + LLM)

```
                    ┌─────────────────┐
                    │  Входная цель   │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
    ┌─────────┴──────────┐      ┌───────────┴──────────┐
    │   SMART Scoring    │      │    LLM Processing    │
    │   (100% rules)     │      │   (GPT-4o-mini)      │
    │                    │      │                      │
    │ • Specificity      │      │ • OKR Mapping        │
    │ • Measurability    │      │ • Goal Rewriting     │
    │ • Achievability    │      │ • Goal Generation    │
    │ • Relevance        │      │                      │
    │ • Time-bound       │      │  Graceful Degradation│
    │                    │      │  (no key → fallback) │
    └─────────┬──────────┘      └───────────┬──────────┘
              │                             │
              └──────────────┬──────────────┘
                             │
                    ┌────────┴────────┐
                    │  Combined       │
                    │  SMART+OKR      │
                    │  Response       │
                    └─────────────────┘
```

---

## 📊 Критерии оценки хакатона (§6)

| Критерий | Вес | Наша реализация |
|----------|-----|-----------------|
| **Качество оценки целей** | 25% | SMART-scoring (rules.py: 300+ строк), стратегическая связка, тип цели, OKR-маппинг, 100% accuracy на 100 тестовых целей |
| **Качество генерации целей** | 25% | RAG-пайплайн + GPT-4o-mini, привязка к ВНД/стратегии, авто-переформулировка при score < 0.7, каскадирование от руководителя |
| **UX интерфейса** | 15% | React 18 SPA: Dashboard, Evaluate, Generate — наглядная обратная связь по каждому критерию |
| **Качество RAG-пайплайна** | 15% | Векторный поиск (TF-IDF + cosine + keyword overlap), chunk-based retrieval, привязка к конкретному фрагменту ВНД |
| **Архитектура и API** | 10% | FastAPI + Swagger, чистый код, DI-контейнер, абстракции Storage/Vector, Docker Compose |
| **Аналитика и дашборд** | 10% | Дашборд руководителя: сводные KPI, сравнительные bar-чарты (SMART + стратег. доля), pie-chart зрелости, рейтинг-таблица подразделений с цветовой кодировкой, индекс зрелости (F-22), статистика данных §4.2, dropdown-селекторы вместо ID |

---

## 🧪 Инструкция для заказчика: как проверить проект

### Быстрый старт (3 минуты)

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. (Опционально) Установить ключ OpenAI для LLM
# Windows PowerShell:
$env:OPENAI_API_KEY = "sk-proj-ваш-ключ"
# Linux/Mac:
export OPENAI_API_KEY="sk-proj-ваш-ключ"

# 3. Запустить сервер
cd backend_project
uvicorn app.main:app --host 0.0.0.0 --port 8899

# 4. Открыть Swagger UI в браузере
# http://localhost:8899/docs
```

> ℹ️ **Без ключа OpenAI** проект полностью работоспособен — используется rule-based fallback (graceful degradation).
> **С ключом** — генерация и переписывание целей через GPT-4o-mini, OKR-маппинг через LLM.

### Пошаговая проверка через Swagger UI

Откройте **http://localhost:8899/docs** — интерактивная автодокументация API.

#### 1️⃣ Проверка оценки слабой цели

Эндпоинт: **POST /api/v1/goals/evaluate** → нажать "Try it out"

```json
{
  "employee_id": "emp_1",
  "goal_text": "Улучшить работу отдела",
  "quarter": "Q2",
  "year": 2026
}
```

**Ожидаемый результат:** `overall_score < 0.5`, рекомендации по улучшению, предложение переписанной цели.

#### 2️⃣ Проверка оценки сильной SMART-цели

```json
{
  "employee_id": "emp_1",
  "goal_text": "До 30.06 сократить средний срок согласования HR-заявок с 5 до 3 рабочих дней за счет цифровизации маршрута согласования",
  "quarter": "Q2",
  "year": 2026
}
```

**Ожидаемый результат:** `overall_score >= 0.8`, `alignment_level = "strategic"`, `goal_type = "impact-based"`.

#### 3️⃣ Генерация целей

Эндпоинт: **POST /api/v1/goals/generate**

```json
{
  "employee_id": "emp_4",
  "quarter": "Q2",
  "year": 2026,
  "count": 3,
  "focus": "подбор и адаптация персонала"
}
```

**Ожидаемый результат:** 3 SMART-совместимые цели для рекрутера с привязкой к документам.

#### 4️⃣ Пакетная оценка целей сотрудника

Эндпоинт: **POST /api/v1/goals/evaluate-batch**

```json
{
  "employee_id": "emp_1",
  "quarter": "Q2",
  "year": 2026,
  "goals": [
    { "title": "До 30.06 довести долю KPI-привязанных целей до 85%", "weight": 30 },
    { "title": "До конца Q2 сократить срок согласования заявок до 3 дней", "weight": 30 },
    { "title": "Улучшить процессы в отделе", "weight": 40 }
  ]
}
```

**Ожидаемый результат:** средний SMART-индекс, слабые критерии, алерты по весу.

#### 5️⃣ Каскадирование целей от руководителя

Эндпоинт: **POST /api/v1/goals/cascade**

```json
{
  "manager_id": "emp_mgr",
  "quarter": "Q2",
  "year": 2026,
  "count_per_employee": 3
}
```

**Ожидаемый результат:** Цели для каждого из 5 подчинённых, каскадированные от целей руководителя.

#### 6️⃣ Индекс зрелости подразделения

Эндпоинт: **GET /api/v1/dashboard/departments/dep_hr/maturity?quarter=Q2&year=2026**

**Ожидаемый результат:** `maturity_index`, `maturity_level`, распределение целей, рекомендации для руководителя.

#### 7️⃣ Загрузка собственных документов (ВНД)

Эндпоинт: **POST /api/v1/documents/ingest**

```json
{
  "documents": [
    {
      "doc_id": "MY-DOC-01",
      "doc_type": "vnd",
      "title": "ВНД по охране труда",
      "content": "Обеспечить проведение инструктажей по ТБ для 100% сотрудников. Снизить количество инцидентов на производстве до нуля. Ежеквартальный аудит условий труда обязателен.",
      "owner_department_id": "dep_ops",
      "department_scope": ["dep_ops", "dep_hr"],
      "keywords": ["охрана труда", "ТБ", "инструктаж", "инциденты"]
    }
  ]
}
```

**Ожидаемый результат:** Документ индексирован, последующие запросы учитывают этот ВНД.

### Доступные тестовые сотрудники

| ID | Имя | Должность | Подразделение |
|----|-----|-----------|---------------|
| `emp_mgr` | Aidos S. | Production Manager | HR / Production Block |
| `emp_1` | Aigerim S. | HR Business Partner | HR / Production Block |
| `emp_2` | Dana M. | L&D Specialist | Learning & Development |
| `emp_3` | Marat K. | C&B Specialist | Compensation & Benefits |
| `emp_4` | Saltanat B. | Recruiter | Recruitment & Staffing |
| `emp_5` | Nurzhan T. | HR Analyst | HR / Production Block |

### Доступные подразделения (8 шт.)

| ID | Название |
|----|----------|
| `dep_hr` | HR / Production Block |
| `dep_lnd` | Learning & Development |
| `dep_ops` | Production Operations |
| `dep_comp` | Compensation & Benefits |
| `dep_rec` | Recruitment & Staffing |
| `dep_fin` | Finance & Budgeting |
| `dep_it` | IT & Digital |
| `dep_legal` | Legal & Compliance |

### Файл с готовыми тестовыми сценариями

В файле **`qa/customer_test_scenarios.json`** подготовлены **14 готовых сценариев** для проверки всех эндпоинтов. Можно копировать JSON-запросы прямо в Swagger UI.

### Запуск автоматических тестов

```bash
cd backend_project

# Контрактные тесты (10 тестов)
python qa/run_api_contract_tests.py

# Быстрый интеграционный тест (15 эндпоинтов)
python qa/quick_test.py

# Диагностический тест (100 целей: 50 bad + 50 good)
python qa/run_diagnostic_50.py

# LLM интеграционные тесты (требуется OPENAI_API_KEY)
python qa/test_llm_integration.py
```

---

## 📊 Результаты тестирования

### Диагностический тест (100 синтетических целей)

| Метрика | Значение |
|---------|----------|
| **Общая точность** | **100.0%** |
| Плохие цели правильно определены | 50/50 (100%) |
| Хорошие цели правильно определены | 50/50 (100%) |
| Средний score плохих целей | 0.408 |
| Средний score хороших целей | 0.860 |
| Разделение (gap) | **0.452** |
| False Positives / Negatives | 0 / 0 |

### API контрактные тесты: **10/10** ✅

### LLM интеграционные тесты: **23/23** ✅

---

## 📥 Формат входных и выходных данных (§3.1.3, §3.2.3)

### Вход: Оценка цели

```json
{
  "employee_id": "string (FK → сотрудник)",
  "goal_text": "string (формулировка цели)",
  "quarter": "string (Q1–Q4)",
  "year": "int (2024–2100)"
}
```

### Выход: Оценка цели (§3.1.3)

```json
{
  "scores": {
    "specific": 0.95,
    "measurable": 0.92,
    "achievable": 0.78,
    "relevant": 0.79,
    "timebound": 0.91
  },
  "overall_score": 0.87,
  "alignment_level": "strategic",
  "goal_type": "impact-based",
  "methodology": "SMART+OKR",
  "recommendations": ["Рекомендация 1", "Рекомендация 2"],
  "rewrite": "Улучшенная формулировка цели",
  "source": {
    "doc_id": "DOC-03",
    "title": "Стратегия цифровизации",
    "doc_type": "strategy",
    "fragment": "Релевантный фрагмент",
    "score": 0.31
  },
  "achievability": {
    "is_achievable": true,
    "confidence": 0.7,
    "historical_avg_score": 0.82,
    "similar_goals_found": 3
  },
  "okr_mapping": {
    "objective": "Стратегический Objective",
    "key_results": ["KR1: ...", "KR2: ...", "KR3: ..."],
    "ambition_score": 8.0,
    "transparency_score": 9.0,
    "okr_recommendation": "Рекомендация по OKR"
  }
}
```

### Выход: Генерация целей (§3.2.3)

```json
[
  {
    "title": "Сгенерированная SMART-цель",
    "score": 0.88,
    "alignment_level": "strategic",
    "goal_type": "impact-based",
    "methodology": "SMART+OKR (LLM)",
    "rationale": "Контекст: почему предложена эта цель",
    "source": {
      "doc_id": "DOC-01",
      "title": "Название ВНД / стратегии",
      "doc_type": "strategy",
      "fragment": "Релевантный фрагмент",
      "score": 0.18
    }
  }
]
```

---

## 🚀 Установка и запуск

### Требования

- **Python** 3.11+
- **Node.js** 18+ (для frontend)
- **Docker** и **Docker Compose** (опционально)

### Backend — быстрый старт

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/Mac
pip install -r requirements.txt
cd backend_project
uvicorn app.main:app --host 0.0.0.0 --port 8899 --reload
```

Swagger UI: **http://localhost:8899/docs**

### С LLM (OpenAI)

```bash
$env:OPENAI_API_KEY = "sk-proj-..."     # Windows
export OPENAI_API_KEY="sk-proj-..."     # Linux/Mac
uvicorn app.main:app --host 0.0.0.0 --port 8899 --reload
```

### Production (Docker Compose)

```bash
cd backend_project
cp .env.example .env    # заполнить значения
docker-compose up -d
```

### Frontend

```bash
cd backend_project/frontend
npm install && npm run dev    # http://localhost:5173
```

---

## ⚙️ Конфигурация

Все настройки через переменные окружения (шаблон: `.env.example`):

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `STORAGE_BACKEND` | memory | `memory` / `postgres` |
| `VECTOR_BACKEND` | memory | `memory` / `qdrant` |
| `OPENAI_API_KEY` | — | API-ключ OpenAI (опционально) |
| `OPENAI_MODEL` | gpt-4o-mini | Модель OpenAI |
| `POSTGRES_HOST` | localhost | Хост PostgreSQL |
| `QDRANT_URL` | — | URL Qdrant |

---

## 📁 Структура проекта

```
goalcraft-ai/
├── requirements.txt              # Python-зависимости
├── README.md                     # Документация
├── .env.example                  # Шаблон конфигурации (§10)
├── data/                         # SQL-дамп организаторов (§4.2)
│   └── README.md                 # Инструкция по загрузке дампа
├── scripts/
│   └── load_dump.py              # Загрузчик SQL-дампа (auto-verify)
├── backend_project/
│   ├── .env.example              # Шаблон конфигурации
│   ├── docker-compose.yml        # Docker orchestration (+ dump auto-import)
│   ├── app/
│   │   ├── main.py               # FastAPI entry point
│   │   ├── container.py          # DI container
│   │   ├── api/routes.py         # 13 REST endpoints
│   │   ├── core/config.py        # Environment configuration
│   │   ├── models/schemas.py     # Pydantic models (все 13 таблиц §4.2)
│   │   ├── services/
│   │   │   ├── engine.py         # GoalEngine (870+ lines)
│   │   │   ├── rules.py          # SMART rules (300+ lines)
│   │   │   └── llm.py            # OpenAI LLM (244 lines)
│   │   ├── storage/
│   │   │   ├── memory.py         # Demo: 8 depts, 6 employees, 10 docs, 18 goals
│   │   │   └── postgres.py       # PostgreSQL store (13 таблиц §4.2)
│   │   └── vector/
│   │       ├── memory_vector.py  # In-memory vector search
│   │       └── qdrant_vector.py  # Qdrant vector store
│   ├── frontend/src/             # React 18 + TypeScript + Vite
│   └── qa/
│       ├── customer_test_scenarios.json  # 14 тестовых сценариев
│       ├── quick_test.py                 # Быстрый тест (15 эндпоинтов)
│       ├── run_api_contract_tests.py     # 10 контрактных тестов
│       └── fixtures/                     # 100 тестовых целей
```

---

## 📄 Лицензия

MIT License — свободное использование в образовательных и коммерческих целях.
