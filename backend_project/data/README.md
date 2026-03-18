# Data Directory

Поместите `.sql` дамп от организаторов хакатона в эту папку.

## Формат дампа

Файл `mock_smart_1.sql` — PostgreSQL custom-format дамп (PGDMP).
Для его загрузки используется `pg_restore`, а НЕ `psql -f`.

## Загрузка дампа

### Вариант 1: Docker (автоматически)
Файл будет автоматически загружен через `pg_restore` при первом запуске:
```bash
cp /path/to/mock_smart_1.sql data/
docker compose up --build
```

### Вариант 2: Python скрипт (локально)
```bash
# Убедитесь, что PostgreSQL запущен и БД создана
createdb -U postgres hr_goal_ai
python scripts/load_dump.py data/mock_smart_1.sql
```

### Вариант 3: pg_restore напрямую
```bash
pg_restore --no-owner --no-privileges -U postgres -d hr_goal_ai data/mock_smart_1.sql
```

### Проверка загрузки
```bash
python scripts/load_dump.py --verify-only
```

## Ожидаемые таблицы (§4.2 ТЗ)

| Таблица | Записей | Описание |
|---------|---------|----------|
| departments | 8 | Подразделения |
| positions | 25 | Должности |
| employees | 450 | Сотрудники |
| documents | 160 | ВНД, стратегии, KPI |
| goals | 9,000 | Цели сотрудников |
| projects | 34 | Проекты |
| systems | 10 | ИТ-системы |
| project_systems | 65 | Связь проект↔система |
| employee_projects | 886 | Связь сотрудник↔проект |
| goal_events | 30,789 | История изменений целей |
| goal_reviews | 4,305 | Рецензии на цели |
| kpi_catalog | 13 | Каталог KPI |
| kpi_timeseries | 2,112 | Временные ряды KPI |
