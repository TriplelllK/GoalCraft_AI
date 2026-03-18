# 🎯 GoalCraft AI — HR Performance Management Platform

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react" alt="React">
  <img src="https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript" alt="TypeScript">
  <img src="https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai" alt="OpenAI">
  <img src="https://img.shields.io/badge/Tests-251-brightgreen" alt="Tests">
  <img src="https://img.shields.io/badge/Accuracy-99%25-brightgreen" alt="Accuracy">
  <img src="https://img.shields.io/badge/LOC-8275-informational" alt="LOC">
</p>

**GoalCraft AI** — интеллектуальная платформа для управления целями сотрудников (Performance Management), которая автоматически оценивает, генерирует и улучшает рабочие цели по комбинированной методологии **SMART + OKR** с использованием гибридного подхода: детерминированные правила + LLM (GPT-4o-mini) + RAG-поиск по корпоративным документам.

> 🏆 Проект создан в рамках хакатона по теме «Внедрение ИИ в HR-процессы»
> 📖 Подробная техническая документация: [backend_project/README.md](backend_project/README.md)

---

## 📋 Содержание

1. [Соответствие ТЗ](#-соответствие-тз)
2. [Архитектура](#️-архитектура)
3. [Критерии оценки хакатона](#-критерии-оценки-хакатона-6)
4. [Инструкция для заказчика](#-инструкция-для-заказчика-как-проверить-проект)
5. [Результаты тестирования](#-результаты-тестирования)
6. [Установка и запуск](#-установка-и-запуск)
7. [Конфигурация](#️-конфигурация)
8. [Структура проекта](#-структура-проекта)

---

## 📋 Соответствие ТЗ

### Компонент A: AI-оценка качества и релевантности целей (§3.1)

| Требование ТЗ | Реализация | Статус |
|----------------|-----------|--------|
| SMART-оценка по 5 критериям (S/M/A/R/T) | `rules.py`: 40+ глаголов, 60+ объектов, regex-паттерны, 313 строк | ✅ |
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
| **F-20** | Достижимость на основе исторических данных (Jaccard similarity, F-20) | ✅ |
| **F-21** | Проверка дублирования (в batch + при генерации per §3.2.2 step 4) | ✅ |
| **F-22** | Индекс зрелости подразделения (maturity_index + maturity_level) | ✅ |

### Логика генерации (§3.2.2)

| Шаг | Описание | Статус |
|-----|----------|--------|
| 1. Retrieval (RAG) | Гибридный поиск: n-gram cosine × 0.40 + BM25 × 0.35 + keyword × 0.15 + doc_type × 0.10 | ✅ |
| 2. Контекстуализация | Должность + подразделение + KPI + проекты + цели руководителя | ✅ |
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
| Alert Manager (уведомления) | ⭕ Опционально | ✅ |
| История изменений целей (F-15) | ⭕ Опционально | ✅ |

### Модель данных (§2.1, §2.2) — 13 таблиц, 30 Pydantic-моделей

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

Система поддерживает все **13 таблиц** из §4.2 + синтетический генератор **47,857 записей** для тестирования:

| Таблица | Записей (demo) | Записей (synthetic) | Описание |
|---------|---------------|---------------------|----------|
| departments | 8 | 8 | Подразделения |
| positions | 8 | 25 | Должности и грейды |
| employees | 6 | 450 | Сотрудники с иерархией |
| documents | 10 | 160 | ВНД, стратегии, KPI-фреймворки |
| goals | 18 | 9,000 | Цели сотрудников за все периоды |
| projects | — | 34 | Проекты компании |
| systems | — | 10 | ИТ-системы |
| project_systems | — | 65 | Связь проект↔система |
| employee_projects | — | 886 | Связь сотрудник↔проект (роль, %) |
| goal_events | — | 30,789 | Журнал изменений целей (F-15) |
| goal_reviews | — | 4,305 | Рецензии руководителей на цели |
| kpi_catalog | — | 13 | Каталог KPI (название, единица) |
| kpi_timeseries | — | 2,112 | Временные ряды KPI по подразделениям |
| **ИТОГО** | **50** | **47,857** | |

**Загрузка дампа:**
```bash
# Вариант 1: Docker (автоматически при первом запуске)
cp hackathon_dump.sql backend_project/data/
docker compose up --build

# Вариант 2: psql
psql -U postgres -d hr_goal_ai -f hackathon_dump.sql

# Проверка загрузки через API:
# GET /api/v1/data/stats — покажет количество записей по каждой из 13 таблиц
```

### Технический стек (§4.1)

| Требование ТЗ | Наша реализация | Обоснование |
|----------------|----------------|-------------|
| PostgreSQL | ✅ PostgreSQL 17 | Production-ready, 13 нормализованных таблиц, Docker Compose |
| ChromaDB / Qdrant / FAISS | ✅ Qdrant + Memory fallback | Qdrant (production): REST API + Docker. Memory (demo): zero-config |
| Python, HuggingFace | ✅ Python + OpenAI GPT-4o-mini | GPT-4o-mini: лучшее соотношение цена/качество для русского языка |
| Embeddings | ✅ N-gram feature hashing (512d) + BM25 hybrid | Zero-dependency, ~1000× быстрее BERT, offline-ready |
| FastAPI / Flask | ✅ FastAPI + Pydantic v2 | Async, автодокументация Swagger, 30 типизированных моделей |
| React / Vue.js | ✅ React 18 + TypeScript + Vite + Recharts | SPA: 5 страниц, 7 компонентов, интерактивные графики |

---

## 🏗️ Архитектура

### Общая схема (§5)

```
┌─────────────────────────────────────────────────────────────────┐
│                  React 18 + TypeScript + Vite                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌────────┐  │
│  │Dashboard │ │ Evaluate │ │ Generate │ │ Cascade │ │Maturity│  │
│  └────┬─────┘ └─────┬────┘ └────┬─────┘ └────┬────┘ └───┬────┘  │
│       └─────────────┼───────────┼────────────┘          │       │
│                     │  HTTP REST API (Vite proxy)       │       │
└─────────────────────┼───────────┼───────────────────────┘───────┘
                      │           │
┌─────────────────────┼───────────┼───────────────────────────────┐
│                FastAPI Backend (17 endpoints)                   │
│  ┌──────────────────┴───────────┴────────────────────────────┐  │
│  │                API Router (routes.py, 179 lines)          │  │
│  │  /health  /evaluate  /generate  /rewrite  /batch          │  │
│  │  /cascade /dashboard /maturity /ingest /context           │  │
│  │  /history  /data/stats  /notifications  /departments      │  │
│  └──────────────────┬────────────────────────────────────────┘  │
│  ┌──────────────────┴────────────────────────────────────────┐  │
│  │             GoalEngine (engine.py, 989 lines)             │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐   │  │
│  │  │ SMART Rules  │  │  LLM Service │  │  RAG / Vector  │   │  │
│  │  │ (rules.py)   │  │  (llm.py)    │  │  Hybrid Search │   │  │
│  │  │ 313 lines    │  │  GPT-4o-mini │  │  N-gram + BM25 │   │  │
│  │  │ Deterministic│  │  210 lines   │  │  188 lines     │   │  │
│  │  └──────────────┘  └──────────────┘  └────────────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────┐  ┌───────────────────────────────┐    │
│  │   Storage Layer      │  │    Vector Store Layer         │    │
│  │  Memory (503 lines)  │  │  Memory (188 lines) — demo    │    │
│  │  Postgres (569 lines)│  │  Qdrant (175 lines) — prod    │    │
│  └──────────────────────┘  └───────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Dual-mode архитектура

Система работает в двух режимах **без изменения кода**:

| | **Demo mode** (по умолчанию) | **Production mode** |
|--|-----|------|
| Storage | In-memory (8 отделов, 6 сотрудников, 18 целей) | PostgreSQL 17 (13 таблиц) |
| Vector | N-gram hashing + BM25 (zero-config) | Qdrant (Docker) |
| LLM | Rule-based fallback (offline) | GPT-4o-mini (OpenAI API) |
| Запуск | `uvicorn app.main:app` | `docker compose up` |

Переключение через переменные окружения — ни одна строка кода не меняется.

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
    │ • Relevance + RAG  │      │                      │
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
| **Качество оценки целей** | 25% | SMART-scoring (rules.py: 313 строк), RAG-контекст, OKR-маппинг, историческая достижимость (F-20), **99% accuracy** на 100 тестовых целей |
| **Качество генерации целей** | 25% | RAG hybrid search + GPT-4o-mini, привязка к ВНД/стратегии, auto-rewrite при score < 0.7, каскадирование (F-14) |
| **UX интерфейса** | 15% | React 18 SPA: 5 страниц (Dashboard, Evaluate, Generate, Cascade, Maturity), Recharts графики, Alert Manager |
| **Качество RAG-пайплайна** | 15% | Sentence-aware chunking (300/50), N-gram feature hashing (512d), BM25, hybrid scoring formula |
| **Архитектура и API** | 10% | FastAPI + Swagger, 17 эндпоинтов, DI-контейнер, 30 Pydantic-моделей, Docker Compose, dual-mode |
| **Аналитика и дашборд** | 10% | Grouped bar chart, maturity pie chart, ranking table, индекс зрелости (F-22), Alert Manager (6 типов уведомлений) |

---

## 🧪 Инструкция для заказчика: как проверить проект

### Быстрый старт (3 минуты)

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/TriplelllK/GoalCraft_AI.git
cd GoalCraft_AI/backend_project

# 2. (Опционально) Подключите LLM — укажите ключ в .env
cp .env.example .env
# Отредактируйте .env — укажите OPENAI_API_KEY

# 3. Запустите все сервисы (API + PostgreSQL + Qdrant + Frontend)
docker compose up --build -d
```

### Порядок проверки после запуска

| # | Проверка | Команда / URL | Ожидаемый результат |
|---|----------|---------------|---------------------|
| 1 | **Health** | `curl http://localhost:8080/health` | `"mode": "hackathon-dump"` — дамп загрузился, 47K записей |
| 2 | **Swagger UI** | http://localhost:8080/docs | Интерактивная документация API, все 16+ эндпоинтов |
| 3 | **Frontend** | http://localhost:5173 | Дашборд, оценка целей, генерация, каскадирование |
| 4 | **Smoke-тест** | `cd qa && python smoke_demo.py` | Все тесты проходят, API отвечает корректно |

> ℹ️ **Без ключа OpenAI** проект полностью работоспособен — используется rule-based fallback (graceful degradation).
> **С ключом** — генерация и переписывание через GPT-4o-mini, OKR-маппинг через LLM.

### Пошаговая проверка через Swagger UI

Откройте **http://localhost:8080/docs** — интерактивная автодокументация API.

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

**Ожидаемый результат:** `maturity_index`, `maturity_level`, распределение целей, рекомендации.

#### 7️⃣ Alert Manager

Эндпоинт: **GET /api/v1/notifications?quarter=Q2&year=2026**

**Ожидаемый результат:** Список уведомлений: critical (< 3 целей, вес ≠ 100%), warning (нет целей, дубликаты).

#### 8️⃣ Загрузка собственных документов (ВНД)

Эндпоинт: **POST /api/v1/documents/ingest**

```json
{
  "documents": [
    {
      "doc_id": "MY-DOC-01",
      "doc_type": "vnd",
      "title": "ВНД по охране труда",
      "content": "Обеспечить проведение инструктажей по ТБ для 100% сотрудников. Снизить количество инцидентов на производстве до нуля.",
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
| `emp_mgr` | Aidos S. | Production Manager (G12) | HR / Production Block |
| `emp_1` | Aigerim S. | HR Business Partner (G10) | HR / Production Block |
| `emp_2` | Dana M. | L&D Specialist (G9) | Learning & Development |
| `emp_3` | Marat K. | C&B Specialist (G9) | Compensation & Benefits |
| `emp_4` | Saltanat B. | Recruiter (G8) | Recruitment & Staffing |
| `emp_5` | Nurzhan T. | HR Analyst (G9) | HR / Production Block |

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

---

## 📊 Результаты тестирования

### 7 тестовых сьютов — 251 тест, 99.6% pass rate

| Тест-сьют | Тестов | Результат | Описание |
|-----------|--------|-----------|----------|
| **Contract Tests** | 15 | ✅ **15/15** | Схемы ответов, типы полей, диапазоны значений |
| **Comprehensive QA** | 61 | ✅ **61/61** | Schema + API + Performance + Edge Cases + Data Integrity + Dashboard |
| **Frontend Functional** | 34 | ✅ **34/34** | Все API-контракты фронтенда, build-артефакты |
| **Smoke Endpoints** | 17 | ✅ **17/17** | 17 эндпоинтов, status 200 + ключевые поля |
| **Quick Tests** | 16 | ✅ **16/16** | Все эндпоинтов быстрой проверкой |
| **Demo Tests** | 8 | ✅ **8/8** | Сценарии демо-режима |
| **Diagnostic (accuracy)** | 100 | ✅ **99/100** | 50 плохих + 50 хороших целей |
| **ИТОГО** | **251** | **250/251** | **99.6% pass rate** |

### Диагностика точности — 100 целей

| Метрика | Значение |
|---------|----------|
| **Общая точность** | **99%** (99/100) |
| Плохие цели правильно определены | 50/50 (100%) |
| Хорошие цели правильно определены | 49/50 (98%) |
| Средний score плохих целей | 0.409 |
| Средний score хороших целей | 0.863 |
| Разделение (gap) | **0.454** |
| False Positives | 1 (пограничный случай, score=0.60) |

### Тестирование на синтетических данных (§4.2)

Comprehensive QA загружает **47,857 синтетических записей** (13 таблиц) и проверяет:
- Корректность API-контрактов на больших объёмах данных
- Performance: health < 100ms, evaluate < 2s, generate < 5s
- Edge cases: пустые подразделения, несуществующие сотрудники
- Data integrity: целостность связей между таблицами

### Запуск тестов

```bash
cd backend_project

# Убедитесь что Docker-контейнеры запущены (docker compose up --build -d)

python qa/run_api_contract_tests.py     # 15/15 контрактных тестов
python qa/run_comprehensive_tests.py    # 61/61 комплексных (+ 47K синтетических записей)
python qa/smoke_endpoints.py            # 17/17 smoke тест всех эндпоинтов
python qa/run_diagnostic_50.py          # 99/100 accuracy (100 целей)
python qa/run_frontend_tests.py         # 34/34 frontend тестов
python qa/quick_test.py                 # 16/16 быстрых тестов
python qa/demo_test.py                  # 8/8 демо тестов
```

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

- **Docker** и **Docker Compose** v2+
- **OPENAI_API_KEY** (опционально — без ключа работает rule-based fallback)

### Запуск через Docker Compose

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/TriplelllK/GoalCraft_AI.git
cd GoalCraft_AI/backend_project

# 2. Настройте переменные окружения
cp .env.example .env
# Отредактируйте .env — укажите OPENAI_API_KEY (опционально)

# 3. Запустите все 4 сервиса (API + PostgreSQL + Qdrant + Frontend)
docker compose up --build -d
```

### Порядок проверки

| # | Проверка | Команда / URL | Ожидаемый результат |
|---|----------|---------------|---------------------|
| 1 | **Health** | `curl http://localhost:8080/health` | `"mode": "hackathon-dump"` — дамп загрузился, 47K записей |
| 2 | **Swagger UI** | http://localhost:8080/docs | Интерактивная документация API, все 16+ эндпоинтов |
| 3 | **Frontend** | http://localhost:5173 | Дашборд, оценка целей, генерация, каскадирование |
| 4 | **Qdrant** | http://localhost:6333/dashboard | Панель управления вектором |
| 5 | **Smoke-тест** | `cd qa && python smoke_demo.py` | Все тесты проходят, API отвечает корректно |

---

## ⚙️ Конфигурация

Все настройки через переменные окружения (шаблон: `.env.example`):

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `STORAGE_BACKEND` | `memory` | `memory` (demo) / `postgres` (production) |
| `POSTGRES_HOST` | `localhost` | Хост PostgreSQL (авто-определяет postgres mode) |
| `POSTGRES_PORT` | `5432` | Порт PostgreSQL |
| `POSTGRES_DB` | `hr_goal_ai` | Имя базы данных |
| `POSTGRES_USER` | `postgres` | Пользователь БД |
| `POSTGRES_PASSWORD` | — | Пароль БД |
| `VECTOR_BACKEND` | `memory` | `memory` (demo) / `qdrant` (production) |
| `QDRANT_URL` | `http://localhost:6333` | URL Qdrant |
| `OPENAI_API_KEY` | — | API-ключ OpenAI (опционально, graceful degradation) |
| `OPENAI_MODEL` | `gpt-4o-mini` | Модель LLM |
| `CORS_ORIGINS` | `*` | CORS-политика |

---

## �️ Загрузка данных хакатона (mock_smart_1.sql)

### Формат дампа

Файл `backend_project/data/mock_smart_1.sql` — **PostgreSQL custom-format** (PGDMP, ~2.7MB).
Содержит 13 таблиц с **47 857 записями** (§4.2 ТЗ):

| Таблица | Записей | Описание |
|---------|---------|----------|
| departments | 8 | Подразделения (ИТ-направления) |
| positions | 25 | Должности с грейдами |
| employees | 450 | Сотрудники + иерархия (manager_id) |
| documents | 160 | ВНД, стратегии, KPI-фреймворки |
| goals | 9 000 | Цели сотрудников за все кварталы |
| goal_events | 30 789 | Журнал изменений целей (F-15) |
| goal_reviews | 4 305 | Рецензии руководителей |
| projects | 34 | Проекты |
| systems | 10 | ИТ-системы |
| project_systems | 65 | Связь проект↔система |
| employee_projects | 886 | Связь сотрудник↔проект |
| kpi_catalog | 13 | Каталог KPI |
| kpi_timeseries | 2 112 | Временные ряды KPI |

### Загрузка дампа

```bash
# Вариант 1: Docker Compose (автоматически при первом запуске)
cp /path/to/mock_smart_1.sql backend_project/data/
cd backend_project && docker compose up --build -d

# Вариант 2: pg_restore вручную
createdb -U postgres hr_goal_ai
pg_restore --no-owner --no-privileges -U postgres -d hr_goal_ai backend_project/data/mock_smart_1.sql

# Вариант 3: Python-скрипт
python backend_project/scripts/load_dump.py backend_project/data/mock_smart_1.sql
```

### Проверка загрузки

```bash
# Через API:
curl http://localhost:8080/api/v1/data/stats
# Ожидаемый ответ: { "departments": 8, "employees": 450, "goals": 9000, ... }

# Через health:
curl http://localhost:8080/health
# mode: "hackathon-dump" — дамп успешно загружен
```

### Автодетекция схемы

PostgresStore автоматически определяет формат данных:
- Если найдена колонка `goals.goal_id` → используется **dump-схема** (§4.2, 13 таблиц)
- Иначе → создаётся **demo-схема** и загружается seed-data

---

## 🔎 Обучение и настройка RAG

### Архитектура RAG-пайплайна

```
Документы (ВНД, стратегии, KPI-фреймворки, политики)
         │
         ▼
┌──────────────────────────┐
│  1. Sentence-aware       │  Разбиение на чанки (max=300 chars, overlap=50)
│     Chunking             │  с учётом границ предложений
└───────────┬──────────────┘
            ▼
┌──────────────────────────┐
│  2. Vectorization        │  N-gram feature hashing → 512-мерный вектор
│     (dual encoder)       │  + BM25 инвертированный индекс
└───────────┬──────────────┘
            ▼
┌──────────────────────────┐
│  3. Hybrid Search        │  score = cosine×0.40 + BM25×0.35
│                          │        + keyword×0.15 + doc_type×0.10
└──────────────────────────┘
```

### Как «обучить» RAG на новых документах

**Шаг 1.** Загрузите документы через API:
```bash
curl -X POST http://localhost:8080/api/v1/documents/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [{
      "doc_id": "VND-001",
      "doc_type": "vnd",
      "title": "Политика управления персоналом",
      "content": "Полный текст документа...",
      "owner_department_id": "dep_hr",
      "department_scope": ["dep_hr", "dep_ops"],
      "keywords": ["управление", "персонал", "KPI"]
    }]
  }'
```

**Шаг 2.** Система автоматически:
1. Разбивает `content` на sentence-aware чанки (300 chars, overlap 50)
2. Строит N-gram hash вектор (SHA-256, 512d) для каждого чанка
3. Добавляет в BM25 индекс (token frequency + IDF)
4. Сохраняет метаданные (dept_scope, doc_type, keywords)

**Шаг 3.** Проверьте индексацию:
```bash
curl http://localhost:8080/health
# indexed_documents: 160+, indexed_chunks: > 500
```

### Типы документов для RAG

| doc_type | Приоритет | Описание |
|----------|-----------|----------|
| `strategy` | Высший (+0.10 бонус) | Стратегические приоритеты компании |
| `vnd` | Высокий (+0.05) | Внутренние нормативные документы |
| `kpi` | Средний | KPI-каталоги и показатели |
| `policy` | Базовый | Корпоративные политики |
| `manager_goal` | Средний | Цели руководителя (для каскадирования) |

### Формула гибридного скоринга

```
final_score = cosine_similarity × 0.40    (семантическое сходство)
            + bm25_normalized   × 0.35    (точное совпадение терминов)
            + keyword_match     × 0.15    (совпадение keywords документа)
            + doc_type_bonus    × 0.10    (приоритет strategy > vnd > kpi)
```

### Метрики качества RAG

| Метрика | Описание | Как проверить |
|---------|----------|---------------|
| Recall@5 | Доля relev. документов в top-5 | Генерация целей → проверить `source.doc_id` |
| Precision@5 | Доля корректных чанков в top-5 | `source.fragment` — содержит ли запрос? |
| Latency p50/p95 | Время поиска | `/health` → performance metrics |
| Coverage | Сколько dept покрыто документами | `/api/v1/data/stats` → documents count |

### Production-режим RAG (Qdrant)

```bash
# В docker-compose.yml уже настроен Qdrant
VECTOR_BACKEND=qdrant
QDRANT_URL=http://qdrant:6333
VECTOR_COLLECTION=hr_goals
VECTOR_SIZE=256
```

При использовании `sentence-transformers` (опционально):
```bash
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

---

## 🤖 Обучение и настройка LLM

### Базовый режим (рекомендуется для MVP)

Система использует **prompt engineering** с GPT-4o-mini:

| Компонент | Файл | Промпт-стратегия |
|-----------|------|-------------------|
| Goal Generator | `llm.py` | System prompt со SMART-критериями + роль + RAG-контекст |
| Goal Rewriter | `llm.py` | Переформулировка с сохранением года/квартала |
| SMART Evaluator | `llm.py` | Оценка по 5 критериям со шкалой 0.0–1.0 |
| OKR Mapper | `llm.py` | Маппинг на Objective + Key Results |

**Настройка LLM:**
```bash
# Windows PowerShell:
$env:OPENAI_API_KEY = "sk-proj-ваш-ключ"
$env:OPENAI_MODEL = "gpt-4o-mini"    # по умолчанию

# Linux/macOS:
export OPENAI_API_KEY="sk-proj-ваш-ключ"
export OPENAI_MODEL="gpt-4o-mini"
```

### Graceful Degradation

| Режим | LLM доступен? | Поведение |
|-------|---------------|-----------|
| **Full** | ✅ Да | SMART rules + LLM generation + LLM rewrite + OKR mapping |
| **Fallback** | ❌ Нет | SMART rules only + rule-based rewrite + template generation |

Система **полностью работоспособна без LLM** — rule-based engine (313 строк) обеспечивает 99% accuracy.

### Продвинутый режим (опционально)

Для fine-tuning или LoRA-адаптации:

1. **Подготовка датасета:**
   - Цели из `goals` (9 000 записей) + `goal_reviews` (4 305 рецензий)
   - Пары: «плохая цель → улучшенная цель» (из goal_events)
   - Экспертные оценки из `goal_reviews.verdict`

2. **LoRA/SFT обучение:**
   ```bash
   # Пример для Hugging Face PEFT
   pip install peft trl
   # Подготовка: export training pairs from DB
   python scripts/export_training_data.py --output training_pairs.jsonl
   # Fine-tune (optional)
   python scripts/finetune_lora.py --base-model mistralai/Mistral-7B-Instruct-v0.3
   ```

3. **Offline оценка:**
   - Корреляция SMART-scores с экспертной разметкой (goal_reviews)
   - Доля структурно корректных JSON-ответов
   - Comparison: rule-based vs LLM vs LLM+LoRA

---

## 📊 Метрики результатов

### A. Оценка качества целей

| Метрика | Значение | Описание |
|---------|----------|----------|
| SMART accuracy | **99%** (99/100) | 50 плохих + 50 хороших целей |
| Средний score плохих | 0.409 | Корректно определяются как слабые |
| Средний score хороших | 0.863 | Корректно определяются как сильные |
| Gap (разделение) | **0.454** | Чёткая граница между плохими и хорошими |
| False Positives | 1 | Пограничный случай (score=0.60) |
| False Negatives | 0 | Все плохие цели выявлены |

### B. Генерация целей

| Метрика | Описание |
|---------|----------|
| SMART-соответствие | Все генерируемые цели проходят threshold (>= 0.7) |
| Привязка к ВНД | Каждая цель имеет `source.doc_id` + `source.fragment` |
| Авто-переформулировка | При score < 0.7 — автоматический rewrite |
| Дубликаты | Проверка Jaccard similarity при генерации |

### C. RAG Pipeline

| Метрика | Описание |
|---------|----------|
| Hybrid search formula | cosine×0.40 + BM25×0.35 + keyword×0.15 + doc_type×0.10 |
| Chunking | sentence-aware, 300 chars, overlap 50 |
| Vector dim | 512 (n-gram feature hashing) |
| Zero-dependency | Работает без GPU, без внешних API |

### D. API Performance

| Эндпоинт | Latency |
|-----------|---------|
| `/health` | < 100ms |
| `/api/v1/goals/evaluate` | < 2s |
| `/api/v1/goals/generate` | < 5s (с LLM), < 1s (rule-based) |
| `/api/v1/dashboard/overview` | < 500ms |

### E. Тестовые сьюты — 251 тест

| Тест-сьют | Тестов | Результат |
|-----------|--------|-----------|
| Contract Tests | 15 | ✅ 15/15 |
| Comprehensive QA | 61 | ✅ 61/61 |
| Frontend Functional | 34 | ✅ 34/34 |
| Smoke Endpoints | 17 | ✅ 17/17 |
| Quick Tests | 16 | ✅ 16/16 |
| Demo Tests | 8 | ✅ 8/8 |
| Diagnostic (accuracy) | 100 | ✅ 99/100 |
| **ИТОГО** | **251** | **250/251 (99.6%)** |

---

## �📁 Структура проекта

```
GoalCraft_AI/
├── requirements.txt                    # Python-зависимости
├── README.md                           # Документация (этот файл)
├── .env.example                        # Шаблон конфигурации
├── .gitignore                          # Git ignore rules
├── backend_project/
│   ├── README.md                       # Техническая презентация (алгоритмы, формулы, RAG)
│   ├── Dockerfile                      # Docker-образ приложения
│   ├── docker-compose.yml              # 3 сервиса: api + PostgreSQL 17 + Qdrant
│   ├── .env.example                    # Переменные окружения
│   ├── app/
│   │   ├── main.py                     # FastAPI entry point
│   │   ├── container.py                # DI-контейнер (Storage → Vector → Engine)
│   │   ├── api/
│   │   │   └── routes.py              # 17 REST-эндпоинтов (179 строк)
│   │   ├── core/
│   │   │   └── config.py             # Конфигурация из env vars (71 строка)
│   │   ├── models/
│   │   │   └── schemas.py            # 30 Pydantic-моделей (297 строк)
│   │   ├── services/
│   │   │   ├── engine.py             # GoalEngine — вся бизнес-логика (989 строк)
│   │   │   ├── rules.py              # SMART-правила, детерминированные (313 строк)
│   │   │   └── llm.py                # LLM-сервис, GPT-4o-mini (210 строк)
│   │   ├── storage/
│   │   │   ├── memory.py             # In-memory хранилище + seed data (503 строки)
│   │   │   └── postgres.py           # PostgreSQL адаптер, 13 таблиц (569 строк)
│   │   └── vector/
│   │       ├── memory_vector.py      # N-gram hashing + BM25 + hybrid (188 строк)
│   │       └── qdrant_vector.py      # Qdrant production vector store (175 строк)
│   ├── frontend/
│   │   ├── package.json              # React 18 + Vite + Recharts
│   │   ├── tsconfig.json             # TypeScript config
│   │   ├── vite.config.ts            # Vite + proxy на backend
│   │   └── src/
│   │       ├── api.ts                # API-клиент, 16 вызовов (65 строк)
│   │       ├── types.ts              # 27 TypeScript-интерфейсов (261 строка)
│   │       ├── App.tsx               # Router: 5 маршрутов
│   │       └── pages/
│   │           ├── DashboardPage.tsx  # Дашборд + графики (277 строк)
│   │           ├── EvaluatePage.tsx   # Оценка + batch (205 строк)
│   │           ├── GeneratePage.tsx   # Генерация целей (105 строк)
│   │           ├── CascadePage.tsx    # Каскадирование (137 строк)
│   │           └── MaturityPage.tsx   # Зрелость (163 строки)
│   └── qa/
│       ├── run_api_contract_tests.py  # 15 контрактных тестов
│       ├── run_comprehensive_tests.py # 61 тест (§4.2, синтетика 47K записей)
│       ├── run_frontend_tests.py      # 34 frontend-теста
│       ├── run_diagnostic_50.py       # 100 целей, accuracy 99%
│       ├── smoke_endpoints.py         # 17 эндпоинтов smoke
│       ├── quick_test.py              # 16 быстрых тестов
│       ├── demo_test.py               # 8 демо-тестов
│       ├── generate_synthetic_db.py   # Генератор 47K записей (666 строк)
│       └── fixtures/                  # Тестовые фикстуры
```

### Метрики проекта

| Метрика | Значение |
|---------|----------|
| Python LOC | **6,757** (30 файлов) |
| TypeScript/TSX LOC | **1,518** (18 файлов) |
| **Всего LOC** | **8,275** (48 файлов) |
| Pydantic-моделей | **30** |
| REST API эндпоинтов | **17** |
| Таблиц БД (§4.2) | **13** |
| Тестов | **251** |
| Pass rate | **99.6%** |
| SMART accuracy | **99%** (100 целей) |

---

## 📄 Лицензия

MIT License — свободное использование в образовательных и коммерческих целях.
