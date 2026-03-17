# Data Directory

Поместите `.sql` дамп от организаторов хакатона в эту папку.

## Загрузка дампа

### Вариант 1: Docker (автоматически)
Файл `.sql` будет автоматически загружен PostgreSQL при первом запуске:
```bash
cp /path/to/hackathon_dump.sql data/
docker compose up --build
```

### Вариант 2: Ручная загрузка
```bash
psql -U postgres -d hr_goal_ai -f data/hackathon_dump.sql
```

### Вариант 3: Через скрипт
```bash
python scripts/load_dump.py data/hackathon_dump.sql
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
