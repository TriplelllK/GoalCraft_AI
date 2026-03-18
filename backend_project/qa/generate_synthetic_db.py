"""
§4.2 Large-Scale Synthetic Database Generator for GoalCraft AI
==============================================================
Generates realistic HR data matching TZ §4.2 hackathon dump volumes:
  departments: 8, positions: 25, employees: 450, documents: 160,
  goals: 9000, projects: 34, systems: 10, project_systems: 65,
  employee_projects: 886, goal_events: 30789, goal_reviews: 4305,
  kpi_catalog: 13, kpi_timeseries: 2112
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── Seed for reproducibility ────────────────────────────────────────
random.seed(42)

# ── Constants ────────────────────────────────────────────────────────

DEPARTMENTS = [
    {"id": "dep_hr", "name": "HR / Production Block", "code": "HR-PB"},
    {"id": "dep_lnd", "name": "Learning & Development", "code": "LND"},
    {"id": "dep_ops", "name": "Production Operations", "code": "OPS"},
    {"id": "dep_comp", "name": "Compensation & Benefits", "code": "C&B"},
    {"id": "dep_rec", "name": "Recruitment & Staffing", "code": "REC"},
    {"id": "dep_fin", "name": "Finance & Budgeting", "code": "FIN"},
    {"id": "dep_it", "name": "IT & Digital", "code": "IT"},
    {"id": "dep_legal", "name": "Legal & Compliance", "code": "LEG"},
]

POSITIONS = [
    {"id": "pos_hrbp", "name": "HR Business Partner", "grade": "G10"},
    {"id": "pos_lnd", "name": "Learning and Development Specialist", "grade": "G9"},
    {"id": "pos_mgr", "name": "Production Manager", "grade": "G12"},
    {"id": "pos_comp", "name": "Compensation and Benefits Specialist", "grade": "G9"},
    {"id": "pos_rec", "name": "Recruiter", "grade": "G8"},
    {"id": "pos_analyst", "name": "HR Analyst", "grade": "G9"},
    {"id": "pos_hrd", "name": "HR Director", "grade": "G14"},
    {"id": "pos_it", "name": "IT Project Manager", "grade": "G11"},
    {"id": "pos_engineer", "name": "Production Engineer", "grade": "G10"},
    {"id": "pos_sr_engineer", "name": "Senior Production Engineer", "grade": "G11"},
    {"id": "pos_lead_engineer", "name": "Lead Production Engineer", "grade": "G13"},
    {"id": "pos_accountant", "name": "Accountant", "grade": "G8"},
    {"id": "pos_sr_accountant", "name": "Senior Accountant", "grade": "G10"},
    {"id": "pos_fin_analyst", "name": "Financial Analyst", "grade": "G10"},
    {"id": "pos_lawyer", "name": "Corporate Lawyer", "grade": "G10"},
    {"id": "pos_sr_lawyer", "name": "Senior Lawyer", "grade": "G12"},
    {"id": "pos_compliance", "name": "Compliance Officer", "grade": "G11"},
    {"id": "pos_dev", "name": "Software Developer", "grade": "G9"},
    {"id": "pos_sr_dev", "name": "Senior Software Developer", "grade": "G11"},
    {"id": "pos_devops", "name": "DevOps Engineer", "grade": "G10"},
    {"id": "pos_pm", "name": "Project Manager", "grade": "G11"},
    {"id": "pos_trainer", "name": "Corporate Trainer", "grade": "G8"},
    {"id": "pos_hr_admin", "name": "HR Administrator", "grade": "G7"},
    {"id": "pos_safety", "name": "Safety Engineer", "grade": "G10"},
    {"id": "pos_shift_lead", "name": "Shift Leader", "grade": "G9"},
]
assert len(POSITIONS) == 25

# Position → department mapping (which positions are common in which departments)
POS_DEPT_MAP = {
    "dep_hr": ["pos_hrbp", "pos_analyst", "pos_hrd", "pos_hr_admin"],
    "dep_lnd": ["pos_lnd", "pos_trainer"],
    "dep_ops": ["pos_mgr", "pos_engineer", "pos_sr_engineer", "pos_lead_engineer", "pos_safety", "pos_shift_lead"],
    "dep_comp": ["pos_comp", "pos_analyst"],
    "dep_rec": ["pos_rec", "pos_hr_admin"],
    "dep_fin": ["pos_accountant", "pos_sr_accountant", "pos_fin_analyst"],
    "dep_it": ["pos_it", "pos_dev", "pos_sr_dev", "pos_devops", "pos_pm"],
    "dep_legal": ["pos_lawyer", "pos_sr_lawyer", "pos_compliance"],
}

# Manager positions per department
MANAGER_POSITIONS = {
    "dep_hr": "pos_hrd",
    "dep_lnd": "pos_lnd",
    "dep_ops": "pos_lead_engineer",
    "dep_comp": "pos_comp",
    "dep_rec": "pos_rec",
    "dep_fin": "pos_sr_accountant",
    "dep_it": "pos_pm",
    "dep_legal": "pos_sr_lawyer",
}

# Kazakh / Russian names
FIRST_NAMES_M = [
    "Айдос", "Марат", "Нуржан", "Алмас", "Ерлан", "Бауыржан", "Данияр",
    "Ержан", "Тимур", "Арман", "Серик", "Асхат", "Руслан", "Дастан",
    "Кайрат", "Мадияр", "Олжас", "Ренат", "Талгат", "Азамат",
    "Жандос", "Нурсултан", "Бекзат", "Канат", "Мухтар", "Сабит",
    "Ильяс", "Жаксылык", "Мейрам", "Дархан",
]
FIRST_NAMES_F = [
    "Айгерим", "Дана", "Салтанат", "Жанна", "Мадина", "Динара", "Асель",
    "Гулнар", "Камила", "Назгуль", "Алия", "Рахия", "Айжан", "Балнур",
    "Гулмира", "Карлыгаш", "Латифа", "Меруерт", "Нургуль", "Сауле",
    "Томирис", "Улболсын", "Фариза", "Жибек", "Зарина", "Индира",
    "Куралай", "Ляззат", "Молдир", "Перизат",
]
LAST_NAMES = [
    "С.", "М.", "К.", "Б.", "Т.", "А.", "Н.", "Р.", "Д.", "Ж.",
    "О.", "Е.", "И.", "П.", "У.", "Г.", "Л.", "Ш.", "Х.", "Ф.",
]

# Quarters
QUARTERS = ["Q1", "Q2", "Q3", "Q4"]
YEARS = [2024, 2025, 2026]

# Goal templates per department (Russian, realistic HR goals)
GOAL_TEMPLATES = {
    "dep_hr": [
        "До {deadline} довести долю целей, привязанных к KPI подразделения, до {pct}%",
        "До {deadline} сократить средний срок согласования HR-заявок с {from_val} до {to_val} рабочих дней",
        "До {deadline} внедрить еженедельный дашборд контроля исполнения HR-процессов",
        "До {deadline} повысить уровень вовлечённости сотрудников (eNPS) до {pct}+",
        "До {deadline} обеспечить каскадирование целей на {pct}% ключевых руководителей",
        "До {deadline} автоматизировать не менее {count} HR-процессов за счет внедрения HRIS",
        "До {deadline} снизить текучесть персонала в критических должностях ниже {pct}%",
        "До {deadline} провести калибровочные сессии для {pct}% подразделений",
    ],
    "dep_lnd": [
        "До {deadline} обеспечить прохождение обязательного обучения не менее {pct}% сотрудников",
        "До {deadline} снизить долю просроченных обучений ниже {pct}% за счет автоматизации напоминаний",
        "До {deadline} обновить программу адаптации новых сотрудников и провести пилот в {count} подразделениях",
        "До {deadline} разработать {count} новых обучающих модулей по развитию лидерских компетенций",
        "До {deadline} внедрить систему оценки эффективности обучения с NPS не ниже {pct}%",
        "До {deadline} обеспечить прохождение обучения по ИБ {pct}% сотрудников HR",
    ],
    "dep_ops": [
        "До {deadline} снизить удельные операционные затраты на {pct}% за счет оптимизации планирования",
        "До {deadline} повысить коэффициент загрузки оборудования до {pct}%",
        "До {deadline} сократить время простоев оборудования на {pct}% за счет внедрения предиктивного обслуживания",
        "До {deadline} обеспечить выполнение плана производства не менее {pct}%",
        "До {deadline} внедрить систему управления инцидентами с SLA не более {count} часов",
        "До {deadline} провести аудит безопасности на {pct}% производственных участков",
    ],
    "dep_comp": [
        "До {deadline} провести анализ рынка заработных плат по {count} ключевым должностям",
        "До {deadline} обновить политику компенсаций и льгот с учётом анализа рынка",
        "До {deadline} снизить долю ошибок в расчёте бонусов ниже {pct}%",
        "До {deadline} обеспечить отклонение ФОТ от бюджета не более {pct}%",
        "До {deadline} пересмотреть грейды для {pct}% позиций по графику",
    ],
    "dep_rec": [
        "До {deadline} сократить средний срок закрытия вакансий с {from_val} до {to_val} рабочих дней",
        "До {deadline} обеспечить укомплектованность критических позиций не ниже {pct}%",
        "До {deadline} внедрить реферальную программу и привлечь не менее {count} кандидатов",
        "До {deadline} увеличить долю внутренних кандидатов на ключевые позиции до {pct}%",
        "До {deadline} автоматизировать скрининг резюме с точностью не ниже {pct}%",
    ],
    "dep_fin": [
        "До {deadline} обеспечить формирование бюджета на {pct}% подразделений в срок",
        "До {deadline} снизить отклонение факта от бюджета до {pct}%",
        "До {deadline} автоматизировать {count} финансовых отчётов",
        "До {deadline} внедрить систему контроля дебиторской задолженности с SLA {count} дней",
        "До {deadline} обеспечить закрытие периода не позднее {count}-го рабочего дня",
    ],
    "dep_it": [
        "До {deadline} обеспечить SLA по внутренним IT-сервисам не ниже {pct}%",
        "До {deadline} мигрировать {count} сервисов в облачную инфраструктуру",
        "До {deadline} снизить количество критических инцидентов на {pct}%",
        "До {deadline} внедрить CI/CD пайплайн для {count} проектов",
        "До {deadline} обеспечить покрытие мониторингом {pct}% критических систем",
    ],
    "dep_legal": [
        "До {deadline} обеспечить согласование {pct}% контрактов в срок не более {count} рабочих дней",
        "До {deadline} провести аудит комплаенс для {pct}% бизнес-процессов",
        "До {deadline} обновить {count} корпоративных политик в соответствии с законодательством",
        "До {deadline} снизить количество юридических рисков категории «высокий» на {pct}%",
        "До {deadline} обеспечить прохождение обучения по комплаенс {pct}% сотрудников",
    ],
}

DOC_TYPES = ["strategy", "vnd", "kpi", "policy", "manager_goal"]

DOC_TEMPLATES = {
    "strategy": [
        "Стратегия развития {area} на {year}-{year2}: {objective}. Приоритеты: {priorities}.",
        "Программа {action} на {year} год: {objective}. Ключевые инициативы: {priorities}.",
    ],
    "vnd": [
        "ВНД по {area}: {objective}. Процедура включает {priorities}.",
        "Регламент {area}: {objective}. Применяется к {scope}.",
    ],
    "kpi": [
        "KPI-фреймворк {area}: {metrics}. Целевые значения на {year}: {targets}.",
    ],
    "policy": [
        "Политика {area}: {objective}. Обязательно для всех {scope}.",
    ],
    "manager_goal": [
        "Цель руководителя: {objective}. Ожидаемый результат: {result}.",
    ],
}

DOC_AREAS = [
    "управления талантами", "цифровизации HR-процессов", "снижения операционных затрат",
    "развития компетенций", "подбора и адаптации персонала", "управления производительностью",
    "компенсаций и льгот", "информационной безопасности", "управления рисками",
    "корпоративной культуры", "организационного развития", "управления знаниями",
    "оценки персонала", "карьерного развития", "кадрового резерва",
    "управления проектами", "финансового планирования", "бизнес-аналитики",
    "автоматизации процессов", "управления изменениями",
]

DOC_OBJECTIVES = [
    "повышение эффективности и прозрачности процессов",
    "обеспечение своевременного исполнения обязательств",
    "снижение рисков и повышение управляемости",
    "оптимизация затрат и ресурсов",
    "развитие ключевых компетенций сотрудников",
    "повышение вовлечённости и удержание талантов",
    "цифровая трансформация ключевых процессов",
    "обеспечение соответствия законодательству",
    "внедрение лучших практик и стандартов",
    "повышение качества управленческих решений",
]

# Projects
PROJECT_NAMES = [
    "HRIS Modernization", "ERP Migration Phase 2", "Production Optimization",
    "Digital HR Platform", "Employee Self-Service Portal", "Recruitment Automation",
    "LMS Implementation", "Payroll System Upgrade", "Safety Management System",
    "Analytics Dashboard", "Mobile HR App", "Performance Management Redesign",
    "Onboarding Automation", "Exit Interview System", "Benefits Portal",
    "Workforce Planning Tool", "Succession Planning", "Training Content Platform",
    "HR Chatbot", "Document Management System", "Compliance Tracking",
    "Time & Attendance System", "Shift Management", "Equipment Tracking",
    "Budget Planning Tool", "Financial Reporting Automation", "Audit Management",
    "Contract Lifecycle Mgmt", "Legal Case Tracker", "Policy Management",
    "Knowledge Base", "Mentorship Platform", "Wellness Program",
    "Carbon Footprint Tracker",
]
assert len(PROJECT_NAMES) == 34

SYSTEMS = [
    {"id": "sys_hris", "name": "SAP SuccessFactors", "type": "HRIS"},
    {"id": "sys_erp", "name": "SAP S/4HANA", "type": "ERP"},
    {"id": "sys_lms", "name": "iSpring Learn", "type": "LMS"},
    {"id": "sys_ats", "name": "Huntflow", "type": "ATS"},
    {"id": "sys_bi", "name": "Power BI", "type": "BI"},
    {"id": "sys_1c", "name": "1C:ZUP", "type": "Payroll"},
    {"id": "sys_jira", "name": "Jira Cloud", "type": "PM"},
    {"id": "sys_confluence", "name": "Confluence", "type": "KnowledgeBase"},
    {"id": "sys_gitlab", "name": "GitLab", "type": "DevOps"},
    {"id": "sys_monitoring", "name": "Zabbix", "type": "Monitoring"},
]
assert len(SYSTEMS) == 10

KPI_CATALOG = [
    {"id": "kpi_001", "name": "Средний SMART-индекс целей", "unit": "%", "description": "Средний балл качества формулировки целей по SMART-методологии"},
    {"id": "kpi_002", "name": "Доля стратегически связанных целей", "unit": "%", "description": "Процент целей с привязкой к стратегии компании"},
    {"id": "kpi_003", "name": "Укомплектованность штата", "unit": "%", "description": "Доля заполненных позиций от штатного расписания"},
    {"id": "kpi_004", "name": "Средний срок закрытия вакансий", "unit": "дней", "description": "Среднее количество рабочих дней от открытия до закрытия вакансии"},
    {"id": "kpi_005", "name": "Текучесть персонала", "unit": "%", "description": "Годовой процент увольнений от среднесписочной численности"},
    {"id": "kpi_006", "name": "Доля прохождения обязательного обучения", "unit": "%", "description": "Процент сотрудников, прошедших обязательное обучение в срок"},
    {"id": "kpi_007", "name": "eNPS (Employee Net Promoter Score)", "unit": "баллы", "description": "Индекс лояльности и вовлечённости сотрудников"},
    {"id": "kpi_008", "name": "Отклонение ФОТ от бюджета", "unit": "%", "description": "Процент отклонения фактических затрат на ФОТ от бюджета"},
    {"id": "kpi_009", "name": "SLA по внутренним сервисам", "unit": "%", "description": "Процент выполнения SLA по внутренним HR-сервисам"},
    {"id": "kpi_010", "name": "Индекс зрелости целеполагания", "unit": "баллы", "description": "Интегральный индекс качества системы целеполагания"},
    {"id": "kpi_011", "name": "Коэффициент загрузки оборудования", "unit": "%", "description": "Процент использования производственных мощностей"},
    {"id": "kpi_012", "name": "Количество производственных инцидентов", "unit": "шт", "description": "Число инцидентов на производстве за период"},
    {"id": "kpi_013", "name": "Среднее время согласования HR-заявок", "unit": "дней", "description": "Среднее время обработки HR-заявок в рабочих днях"},
]
assert len(KPI_CATALOG) == 13

# Event types for goal lifecycle
EVENT_TYPES = [
    "created", "edited", "submitted", "returned", "approved",
    "rejected", "weight_changed", "metric_updated", "deadline_extended",
    "status_changed", "comment_added",
]

REVIEW_VERDICTS = ["approved", "needs_revision", "rejected", "approved_with_comments"]

GOAL_STATUSES = ["draft", "submitted", "approved", "rejected", "in_progress", "completed"]

PROJECT_ROLES = [
    "Руководитель проекта", "Участник рабочей группы", "Куратор",
    "Бизнес-аналитик", "Технический эксперт", "Тестировщик",
    "Консультант", "Ключевой пользователь",
]


def _uid(prefix: str, idx: int) -> str:
    return f"{prefix}_{idx:04d}"


def _deadline_for_quarter(q: str, y: int) -> date:
    ends = {"Q1": (3, 31), "Q2": (6, 30), "Q3": (9, 30), "Q4": (12, 31)}
    m, d = ends[q]
    return date(y, m, d)


def _random_date_in_range(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(0, delta)))


def generate_employees(departments: list[dict], positions: list[dict], target: int = 450) -> list[dict]:
    """Generate employees with realistic hierarchy."""
    employees = []
    emp_idx = 0
    dept_managers: dict[str, str] = {}

    pos_by_id = {p["id"]: p for p in positions}

    # First pass: create a manager for each department
    for dept in departments:
        emp_idx += 1
        mgr_pos = MANAGER_POSITIONS.get(dept["id"], "pos_mgr")
        gender = random.choice(["M", "F"])
        first_name = random.choice(FIRST_NAMES_M if gender == "M" else FIRST_NAMES_F)
        last_name = random.choice(LAST_NAMES)
        emp_id = _uid("emp", emp_idx)
        employees.append({
            "id": emp_id,
            "employee_code": f"E{emp_idx:04d}",
            "full_name": f"{first_name} {last_name}",
            "email": f"emp{emp_idx}@kumkol.kz",
            "department_id": dept["id"],
            "position_id": mgr_pos,
            "manager_id": None,
            "hire_date": str(_random_date_in_range(date(2020, 1, 1), date(2024, 6, 30))),
            "is_active": True,
        })
        dept_managers[dept["id"]] = emp_id

    # Distribute remaining employees across departments
    remaining = target - len(employees)
    # Weighted distribution: HR and OPS get more employees
    weights = {"dep_hr": 3, "dep_lnd": 1.5, "dep_ops": 4, "dep_comp": 1, "dep_rec": 1.5, "dep_fin": 1.5, "dep_it": 2.5, "dep_legal": 1}
    total_w = sum(weights.values())
    dept_counts = {}
    allocated = 0
    for dept in departments[:-1]:
        cnt = int(remaining * weights[dept["id"]] / total_w)
        dept_counts[dept["id"]] = cnt
        allocated += cnt
    dept_counts[departments[-1]["id"]] = remaining - allocated

    for dept in departments:
        dept_positions = POS_DEPT_MAP.get(dept["id"], ["pos_hrbp"])
        mgr_id = dept_managers[dept["id"]]
        for _ in range(dept_counts.get(dept["id"], 0)):
            emp_idx += 1
            gender = random.choice(["M", "F"])
            first_name = random.choice(FIRST_NAMES_M if gender == "M" else FIRST_NAMES_F)
            last_name = random.choice(LAST_NAMES)
            pos_id = random.choice(dept_positions)
            emp_id = _uid("emp", emp_idx)
            employees.append({
                "id": emp_id,
                "employee_code": f"E{emp_idx:04d}",
                "full_name": f"{first_name} {last_name}",
                "email": f"emp{emp_idx}@kumkol.kz",
                "department_id": dept["id"],
                "position_id": pos_id,
                "manager_id": mgr_id,
                "hire_date": str(_random_date_in_range(date(2020, 1, 1), date(2025, 12, 31))),
                "is_active": random.random() > 0.02,  # 2% inactive
            })

    return employees


def generate_documents(departments: list[dict], target: int = 160) -> list[dict]:
    """Generate 160 realistic documents."""
    docs = []
    doc_idx = 0
    dept_ids = [d["id"] for d in departments]

    for _ in range(target):
        doc_idx += 1
        doc_type = random.choice(DOC_TYPES)
        area = random.choice(DOC_AREAS)
        objective = random.choice(DOC_OBJECTIVES)
        owner_dept = random.choice(dept_ids)

        # Build scope: owner + 1-3 related departments
        scope = [owner_dept]
        for _ in range(random.randint(1, 3)):
            candidate = random.choice(dept_ids)
            if candidate not in scope:
                scope.append(candidate)

        title_templates = DOC_TEMPLATES.get(doc_type, DOC_TEMPLATES["policy"])
        title_tmpl = random.choice(title_templates)

        title = f"DOC-{doc_idx:03d}: {doc_type.upper()} — {area.capitalize()}"
        content = title_tmpl.format(
            area=area, year=random.choice([2025, 2026]),
            year2=random.choice([2027, 2028]),
            objective=objective,
            priorities=random.choice(DOC_OBJECTIVES),
            action=random.choice(["оптимизации", "развития", "трансформации"]),
            scope="сотрудников подразделения",
            metrics="ключевые метрики эффективности",
            targets="значения определяются по итогам калибровки",
            result=objective,
        )

        keywords = random.sample(
            ["KPI", "цели", "обучение", "компетенции", "цифровизация", "HR",
             "стратегия", "подбор", "адаптация", "оценка", "бюджет", "ФОТ",
             "текучесть", "вовлечённость", "безопасность", "комплаенс",
             "производство", "автоматизация", "SLA", "мониторинг"],
            k=random.randint(2, 5)
        )

        docs.append({
            "doc_id": f"DOC-{doc_idx:03d}",
            "doc_type": doc_type,
            "title": title,
            "content": content,
            "owner_department_id": owner_dept,
            "department_scope": scope,
            "keywords": keywords,
            "version": f"{random.choice([1, 2, 3])}.{random.randint(0, 5)}",
            "is_active": random.random() > 0.05,
        })

    return docs


def generate_goals(employees: list[dict], departments: list[dict], positions: list[dict], target: int = 9000) -> list[dict]:
    """Generate 9000 goals across multiple quarters."""
    goals = []
    goal_idx = 0
    pos_by_id = {p["id"]: p["name"] for p in positions}
    dept_by_id = {d["id"]: d for d in departments}

    active_emps = [e for e in employees if e.get("is_active", True)]

    # Target distribution: ~20 goals per employee on average (across 5 quarters)
    # Q4-2024, Q1-2025, Q2-2025, Q3-2025, Q4-2025, Q1-2026, Q2-2026
    periods = [
        ("Q4", 2024), ("Q1", 2025), ("Q2", 2025), ("Q3", 2025),
        ("Q4", 2025), ("Q1", 2026), ("Q2", 2026),
    ]

    goals_per_employee_period = max(1, target // (len(active_emps) * len(periods)))

    # Use round-robin to fill goals evenly — keep cycling until target reached
    emp_period_pairs = [(emp, q, y) for emp in active_emps for q, y in periods]
    random.shuffle(emp_period_pairs)
    pair_idx = 0

    while len(goals) < target:
        emp, quarter, year = emp_period_pairs[pair_idx % len(emp_period_pairs)]
        pair_idx += 1

        dept_id = emp["department_id"]
        pos_name = pos_by_id.get(emp["position_id"], "HR Business Partner")
        dept_templates = GOAL_TEMPLATES.get(dept_id, GOAL_TEMPLATES["dep_hr"])

        num_goals = random.randint(2, 4)
        weights = _random_weights(num_goals)

        for g_idx in range(num_goals):
            if len(goals) >= target:
                break
            goal_idx += 1
            tmpl = random.choice(dept_templates)
            dl = _deadline_for_quarter(quarter, year)

            title = tmpl.format(
                deadline=dl.strftime("%d.%m"),
                pct=random.choice([80, 85, 90, 92, 95, 97, 98]),
                from_val=random.choice([5, 7, 10, 15, 30, 45]),
                to_val=random.choice([2, 3, 5, 8, 20, 25, 30]),
                count=random.choice([2, 3, 4, 5, 10, 15, 20]),
            )

            # Status based on quarter
            if year < 2026 or (year == 2026 and quarter == "Q1"):
                status = random.choice(["approved", "approved", "approved", "completed", "rejected"])
            elif quarter == "Q2" and year == 2026:
                status = random.choice(["draft", "submitted", "approved", "in_progress"])
            else:
                status = random.choice(["draft", "submitted"])

            goals.append({
                "id": _uid("goal", goal_idx),
                "employee_id": emp["id"],
                "department_id": dept_id,
                "position": pos_name,
                "title": title,
                "goal_text": title,
                "description": "",
                "metric": "целевой показатель согласно формулировке",
                "deadline": str(dl),
                "status": status,
                "quarter": quarter,
                "year": year,
                "weight": weights[g_idx],
                "reviewer_comment": "",
                "created_at": str(_random_date_in_range(date(year, ({"Q1": 1, "Q2": 4, "Q3": 7, "Q4": 10}[quarter]), 1), dl - timedelta(days=30))),
                "updated_at": "",
            })

    return goals[:target]


def _random_weights(n: int) -> list[float]:
    """Generate n weights that sum to ~100."""
    if n == 1:
        return [100.0]
    raw = [random.randint(10, 50) for _ in range(n)]
    total = sum(raw)
    normalized = [round(w / total * 100, 1) for w in raw]
    # Fix rounding error
    diff = 100.0 - sum(normalized)
    normalized[-1] = round(normalized[-1] + diff, 1)
    return normalized


def generate_projects(target: int = 34) -> list[dict]:
    projects = []
    for idx in range(target):
        start = _random_date_in_range(date(2024, 1, 1), date(2025, 12, 31))
        end = start + timedelta(days=random.randint(60, 365))
        projects.append({
            "id": _uid("proj", idx + 1),
            "name": PROJECT_NAMES[idx],
            "status": random.choice(["active", "active", "active", "completed", "planned"]),
            "start_date": str(start),
            "end_date": str(end),
        })
    return projects


def generate_project_systems(projects: list[dict], systems: list[dict], target: int = 65) -> list[dict]:
    """Link projects to systems (many-to-many)."""
    links = set()
    sys_ids = [s["id"] for s in systems]
    proj_ids = [p["id"] for p in projects]

    while len(links) < target:
        proj = random.choice(proj_ids)
        sys_id = random.choice(sys_ids)
        links.add((proj, sys_id))

    return [{"project_id": p, "system_id": s} for p, s in links]


def generate_employee_projects(employees: list[dict], projects: list[dict], target: int = 886) -> list[dict]:
    """Assign employees to projects."""
    links = []
    active_emps = [e for e in employees if e.get("is_active", True)]
    seen = set()

    while len(links) < target:
        emp = random.choice(active_emps)
        proj = random.choice(projects)
        key = (emp["id"], proj["id"])
        if key in seen:
            continue
        seen.add(key)
        links.append({
            "employee_id": emp["id"],
            "project_id": proj["id"],
            "role": random.choice(PROJECT_ROLES),
            "allocation_percent": random.choice([10, 15, 20, 25, 30, 40, 50, 75, 100]),
            "start_date": proj.get("start_date"),
            "end_date": proj.get("end_date"),
        })

    return links[:target]


def generate_goal_events(goals: list[dict], employees: list[dict], target: int = 30789) -> list[dict]:
    """Generate goal lifecycle events."""
    events = []
    evt_idx = 0
    emp_ids = [e["id"] for e in employees]

    for goal in goals:
        # Each goal has 2-5 events
        num_events = random.randint(2, 5)
        if len(events) + num_events > target:
            num_events = target - len(events)

        statuses = ["draft"]
        for _ in range(num_events):
            evt_idx += 1
            evt_type = random.choice(EVENT_TYPES)
            old_status = statuses[-1]

            if evt_type in ("submitted", "approved", "rejected"):
                new_status = evt_type if evt_type != "submitted" else "submitted"
            elif evt_type == "status_changed":
                new_status = random.choice(GOAL_STATUSES)
            else:
                new_status = old_status

            statuses.append(new_status)

            events.append({
                "id": _uid("evt", evt_idx),
                "goal_id": goal["id"],
                "event_type": evt_type,
                "actor_id": random.choice([goal["employee_id"], random.choice(emp_ids)]),
                "old_status": old_status,
                "new_status": new_status,
                "old_text": "",
                "new_text": "",
                "metadata": "{}",
                "created_at": goal.get("created_at", "2026-01-01"),
            })

        if len(events) >= target:
            break

    return events[:target]


def generate_goal_reviews(goals: list[dict], employees: list[dict], target: int = 4305) -> list[dict]:
    """Generate goal reviews (manager/HR approval cycles)."""
    reviews = []
    rev_idx = 0
    emp_ids = [e["id"] for e in employees if e.get("manager_id") is None]  # Reviewers are managers
    if not emp_ids:
        emp_ids = [e["id"] for e in employees[:10]]

    reviewed_goals = [g for g in goals if g["status"] in ("approved", "rejected", "completed")]
    if not reviewed_goals:
        reviewed_goals = goals

    while len(reviews) < target:
        goal = random.choice(reviewed_goals)
        rev_idx += 1
        reviews.append({
            "id": _uid("rev", rev_idx),
            "goal_id": goal["id"],
            "reviewer_id": random.choice(emp_ids),
            "verdict": random.choice(REVIEW_VERDICTS),
            "created_at": goal.get("created_at", "2026-01-01"),
        })

    return reviews[:target]


def generate_kpi_timeseries(kpi_catalog: list[dict], departments: list[dict], target: int = 2112) -> list[dict]:
    """Generate KPI timeseries data."""
    records = []
    ts_idx = 0
    dept_ids = [d["id"] for d in departments]
    periods = [f"{y}-{q}" for y in [2024, 2025, 2026] for q in ["Q1", "Q2", "Q3", "Q4"]]

    while len(records) < target:
        for kpi in kpi_catalog:
            for dept_id in dept_ids:
                for period in periods:
                    if len(records) >= target:
                        break
                    ts_idx += 1

                    # Generate realistic values based on KPI unit
                    if kpi["unit"] == "%":
                        value = round(random.uniform(50, 99), 1)
                    elif kpi["unit"] == "дней":
                        value = round(random.uniform(2, 45), 1)
                    elif kpi["unit"] == "баллы":
                        value = round(random.uniform(30, 90), 1)
                    elif kpi["unit"] == "шт":
                        value = round(random.uniform(0, 20), 0)
                    else:
                        value = round(random.uniform(10, 100), 1)

                    records.append({
                        "id": _uid("ts", ts_idx),
                        "kpi_id": kpi["id"],
                        "department_id": dept_id,
                        "period": period,
                        "value": value,
                    })
                if len(records) >= target:
                    break
            if len(records) >= target:
                break

    return records[:target]


def generate_all() -> dict:
    """Main entry: generate full §4.2 dataset."""
    print("Generating §4.2 synthetic dataset...")

    departments = DEPARTMENTS
    positions = POSITIONS
    print(f"  departments: {len(departments)}")
    print(f"  positions: {len(positions)}")

    employees = generate_employees(departments, positions, target=450)
    print(f"  employees: {len(employees)}")

    documents = generate_documents(departments, target=160)
    print(f"  documents: {len(documents)}")

    goals = generate_goals(employees, departments, positions, target=9000)
    print(f"  goals: {len(goals)}")

    projects = generate_projects(target=34)
    print(f"  projects: {len(projects)}")

    systems = SYSTEMS
    print(f"  systems: {len(systems)}")

    project_systems = generate_project_systems(projects, systems, target=65)
    print(f"  project_systems: {len(project_systems)}")

    employee_projects = generate_employee_projects(employees, projects, target=886)
    print(f"  employee_projects: {len(employee_projects)}")

    goal_events = generate_goal_events(goals, employees, target=30789)
    print(f"  goal_events: {len(goal_events)}")

    goal_reviews = generate_goal_reviews(goals, employees, target=4305)
    print(f"  goal_reviews: {len(goal_reviews)}")

    kpi_timeseries = generate_kpi_timeseries(KPI_CATALOG, departments, target=2112)
    print(f"  kpi_catalog: {len(KPI_CATALOG)}")
    print(f"  kpi_timeseries: {len(kpi_timeseries)}")

    dataset = {
        "departments": departments,
        "positions": positions,
        "employees": employees,
        "documents": documents,
        "goals": goals,
        "projects": projects,
        "systems": systems,
        "project_systems": project_systems,
        "employee_projects": employee_projects,
        "goal_events": goal_events,
        "goal_reviews": goal_reviews,
        "kpi_catalog": KPI_CATALOG,
        "kpi_timeseries": kpi_timeseries,
    }

    return dataset


def save_dataset(dataset: dict, output_path: Path | None = None) -> Path:
    if output_path is None:
        output_path = ROOT / "qa" / "fixtures" / "synthetic_dump.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nDataset saved to {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
    return output_path


def print_summary(dataset: dict) -> None:
    print("\n§4.2 Dataset Summary:")
    print("=" * 50)
    for table, rows in dataset.items():
        print(f"  {table:25s}: {len(rows):>8,}")
    total = sum(len(v) for v in dataset.values())
    print(f"  {'TOTAL':25s}: {total:>8,}")


if __name__ == "__main__":
    dataset = generate_all()
    save_dataset(dataset)
    print_summary(dataset)
