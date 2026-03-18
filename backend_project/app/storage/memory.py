"""In-memory data store with demo seed data for local / testing runs."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Optional

from app.models.schemas import (
    Department, Document, Employee, Goal, Position,
    GoalEvent, GoalReview, KpiCatalog, KpiTimeseries,
)


class MemoryStore:
    """Pure-Python store that mirrors the PostgresStore API using dicts."""

    def __init__(self) -> None:
        self.departments: dict[str, Department] = {}
        self.positions: dict[str, Position] = {}
        self.employees: dict[str, Employee] = {}
        self._documents: dict[str, Document] = {}
        self._goals: list[Goal] = []
        # §4.2 extended tables
        self._goal_events: list[GoalEvent] = []
        self._goal_reviews: list[GoalReview] = []
        self._kpi_catalog: dict[str, KpiCatalog] = {}
        self._kpi_timeseries: list[KpiTimeseries] = []
        self._employee_projects: list[dict] = []
        self._seed_demo()

    # ── Seed ─────────────────────────────────────────────────────────

    def _seed_demo(self) -> None:
        for dep in [
            Department(id="dep_hr", name="HR / Production Block", code="HR-PB"),
            Department(id="dep_lnd", name="Learning & Development", code="LND"),
            Department(id="dep_ops", name="Production Operations", code="OPS"),
            Department(id="dep_comp", name="Compensation & Benefits", code="C&B"),
            Department(id="dep_rec", name="Recruitment & Staffing", code="REC"),
            Department(id="dep_fin", name="Finance & Budgeting", code="FIN"),
            Department(id="dep_it", name="IT & Digital", code="IT"),
            Department(id="dep_legal", name="Legal & Compliance", code="LEG"),
        ]:
            self.departments[dep.id] = dep

        for pos in [
            Position(id="pos_hrbp", name="HR Business Partner", grade="G10"),
            Position(id="pos_lnd", name="Learning and Development Specialist", grade="G9"),
            Position(id="pos_mgr", name="Production Manager", grade="G12"),
            Position(id="pos_comp", name="Compensation and Benefits Specialist", grade="G9"),
            Position(id="pos_rec", name="Recruiter", grade="G8"),
            Position(id="pos_analyst", name="HR Analyst", grade="G9"),
            Position(id="pos_hrd", name="HR Director", grade="G14"),
            Position(id="pos_it", name="IT Project Manager", grade="G11"),
        ]:
            self.positions[pos.id] = pos

        for emp in [
            Employee(
                id="emp_mgr", employee_code="E0001", full_name="Aidos S.",
                email="aidos@example.com", department_id="dep_hr",
                position_id="pos_mgr", manager_id=None, hire_date=date(2023, 1, 10),
            ),
            Employee(
                id="emp_1", employee_code="E0002", full_name="Aigerim S.",
                email="aigerim@example.com", department_id="dep_hr",
                position_id="pos_hrbp", manager_id="emp_mgr", hire_date=date(2024, 2, 1),
            ),
            Employee(
                id="emp_2", employee_code="E0003", full_name="Dana M.",
                email="dana@example.com", department_id="dep_lnd",
                position_id="pos_lnd", manager_id="emp_mgr", hire_date=date(2024, 3, 12),
            ),
            Employee(
                id="emp_3", employee_code="E0004", full_name="Marat K.",
                email="marat@example.com", department_id="dep_comp",
                position_id="pos_comp", manager_id="emp_mgr", hire_date=date(2024, 5, 15),
            ),
            Employee(
                id="emp_4", employee_code="E0005", full_name="Saltanat B.",
                email="saltanat@example.com", department_id="dep_rec",
                position_id="pos_rec", manager_id="emp_mgr", hire_date=date(2024, 1, 20),
            ),
            Employee(
                id="emp_5", employee_code="E0006", full_name="Nurzhan T.",
                email="nurzhan@example.com", department_id="dep_hr",
                position_id="pos_analyst", manager_id="emp_mgr", hire_date=date(2023, 9, 1),
            ),
        ]:
            self.employees[emp.id] = emp

        for doc in [
            Document(
                doc_id="DOC-01", doc_type="strategy",
                title="Программа снижения операционных затрат",
                content="Снизить удельные операционные затраты по производственным процессам за счет оптимизации планирования и цифровизации. Приоритет квартала — сокращение времени внутренних согласований и повышение прозрачности исполнения.",
                owner_department_id="dep_ops",
                department_scope=["dep_hr", "dep_ops"],
                keywords=["снижение затрат", "цифровизация", "согласование"],
            ),
            Document(
                doc_id="DOC-02", doc_type="vnd",
                title="ВНД по развитию компетенций и обязательного обучения",
                content="Обеспечить своевременное прохождение обязательного обучения и развитие критически значимых компетенций сотрудников. Снизить долю просроченных обучений и автоматизировать напоминания.",
                owner_department_id="dep_lnd",
                department_scope=["dep_hr", "dep_lnd", "dep_ops"],
                keywords=["обучение", "компетенции", "напоминания"],
            ),
            Document(
                doc_id="DOC-03", doc_type="strategy",
                title="Стратегия цифровизации производственных функций",
                content="Приоритет квартала — перевод ручных процессов в цифровой формат и повышение прозрачности исполнения задач. Требуется сократить срок внутренних HR-процессов и повысить управляемость статусов.",
                owner_department_id="dep_hr",
                department_scope=["dep_hr", "dep_ops"],
                keywords=["цифровизация", "HR", "прозрачность"],
            ),
            Document(
                doc_id="DOC-04", doc_type="kpi",
                title="KPI каталога HR-подразделения",
                content="Ключевые KPI подразделения: доля целей, привязанных к KPI, средний срок согласования HR-заявок, доля обязательного обучения, доля стратегически связанных целей.",
                owner_department_id="dep_hr",
                department_scope=["dep_hr"],
                keywords=["KPI", "HR-заявки", "цели"],
            ),
            Document(
                doc_id="DOC-05", doc_type="manager_goal",
                title="Цель руководителя на квартал",
                content="Сократить время внутренних HR-процессов и повысить прозрачность исполнения по обязательному обучению. Обеспечить рост стратегической связки целей сотрудников в производственном блоке.",
                owner_department_id="dep_hr",
                department_scope=["dep_hr"],
                keywords=["руководитель", "прозрачность", "обучение"],
            ),
            Document(
                doc_id="DOC-06", doc_type="policy",
                title="Политика подбора и адаптации персонала",
                content="Обеспечить укомплектованность штата не ниже 95% по критическим позициям. Средний срок закрытия вакансий — не более 30 рабочих дней. Реферальная программа должна обеспечивать не менее 15% от общего потока кандидатов. Программа адаптации — обязательна для всех новых сотрудников в течение первых 90 дней.",
                owner_department_id="dep_rec",
                department_scope=["dep_hr", "dep_rec", "dep_lnd"],
                keywords=["подбор", "адаптация", "вакансии", "реферальная программа", "укомплектованность"],
            ),
            Document(
                doc_id="DOC-07", doc_type="kpi",
                title="KPI-фреймворк направления C&B",
                content="Показатели эффективности компенсаций и льгот: отклонение фактических затрат на ФОТ от бюджета не более 3%, доля ошибок в расчёте бонусов ниже 2%, своевременность пересмотра грейдов — 100% по графику, конкурентоспособность зарплат — медиана рынка ±10%.",
                owner_department_id="dep_comp",
                department_scope=["dep_comp", "dep_hr", "dep_fin"],
                keywords=["компенсации", "бонусы", "грейды", "ФОТ", "бюджет"],
            ),
            Document(
                doc_id="DOC-08", doc_type="strategy",
                title="Стратегия управления талантами 2025–2027",
                content="Стратегические приоритеты: снижение текучести ключевых сотрудников ниже 8%, формирование кадрового резерва на 100% критических позиций, внедрение программы наставничества, повышение eNPS до 70+. Ключевые инициативы: автоматизация HR-аналитики, развитие лидерских компетенций руководителей, программа карьерного развития.",
                owner_department_id="dep_hr",
                department_scope=["dep_hr", "dep_lnd", "dep_rec", "dep_comp"],
                keywords=["текучесть", "кадровый резерв", "наставничество", "eNPS", "таланты"],
            ),
            Document(
                doc_id="DOC-09", doc_type="vnd",
                title="ВНД по проведению оценки персонала (Performance Review)",
                content="Процедура проведения ежеквартальной оценки: калибровочные сессии, формы оценки 360°, шкала оценок, порядок обратной связи. Руководители обязаны провести оценку не позднее 15-го числа месяца после окончания квартала. Результаты оценки влияют на размер квартального бонуса.",
                owner_department_id="dep_hr",
                department_scope=["dep_hr", "dep_ops", "dep_lnd"],
                keywords=["оценка", "performance review", "360", "калибровка", "бонус"],
            ),
            Document(
                doc_id="DOC-10", doc_type="policy",
                title="Политика информационной безопасности персональных данных",
                content="Все персональные данные сотрудников хранятся в зашифрованном виде. Доступ к HR-системам — через SSO с двухфакторной аутентификацией. Аудит доступа проводится ежеквартально. Обучение по ИБ — обязательно для всех сотрудников HR-подразделения.",
                owner_department_id="dep_it",
                department_scope=["dep_hr", "dep_it", "dep_legal"],
                keywords=["безопасность", "персональные данные", "аудит", "SSO"],
            ),
        ]:
            self._documents[doc.doc_id] = doc

        self._goals = [
            # ── Q2 2026 current goals ────────────────────────────────
            Goal(
                id="goal_demo_1", employee_id="emp_1",
                department_id="dep_hr", position="HR Business Partner",
                title="До конца Q2 довести долю целей, привязанных к KPI подразделения, до 85%",
                goal_text="До конца Q2 довести долю целей, привязанных к KPI подразделения, до 85%",
                metric="доля целей привязанных к KPI >= 85%",
                deadline=date(2026, 6, 30),
                quarter="Q2", year=2026, weight=50.0,
            ),
            Goal(
                id="goal_demo_2", employee_id="emp_1",
                department_id="dep_hr", position="HR Business Partner",
                title="До 30.06 сократить средний срок согласования HR-заявок с 5 до 3 рабочих дней",
                goal_text="До 30.06 сократить средний срок согласования HR-заявок с 5 до 3 рабочих дней",
                metric="средний срок согласования <= 3 рабочих дней",
                deadline=date(2026, 6, 30),
                quarter="Q2", year=2026, weight=50.0,
            ),
            # ── Q1 2026 historical goals (emp_1 — HR Business Partner) ──
            Goal(
                id="goal_hist_1", employee_id="emp_1",
                department_id="dep_hr", position="HR Business Partner",
                title="До 31.03 обеспечить прохождение обязательного обучения не менее 95% сотрудников подразделения",
                goal_text="До 31.03 обеспечить прохождение обязательного обучения не менее 95% сотрудников подразделения",
                metric="доля прохождения обучения >= 95%",
                deadline=date(2026, 3, 31),
                quarter="Q1", year=2026, weight=40.0, status="approved",
            ),
            Goal(
                id="goal_hist_2", employee_id="emp_1",
                department_id="dep_hr", position="HR Business Partner",
                title="До конца Q1 снизить долю просроченных HR-заявок ниже 10% за счет автоматизации маршрутов согласования",
                goal_text="До конца Q1 снизить долю просроченных HR-заявок ниже 10% за счет автоматизации маршрутов согласования",
                metric="доля просроченных HR-заявок < 10%",
                deadline=date(2026, 3, 31),
                quarter="Q1", year=2026, weight=30.0, status="approved",
            ),
            Goal(
                id="goal_hist_3", employee_id="emp_1",
                department_id="dep_hr", position="HR Business Partner",
                title="До 31.03 внедрить еженедельный дашборд контроля обязательного обучения",
                goal_text="До 31.03 внедрить еженедельный дашборд контроля обязательного обучения",
                metric="дашборд внедрён и обновляется еженедельно",
                deadline=date(2026, 3, 31),
                quarter="Q1", year=2026, weight=30.0, status="approved",
            ),
            # ── Q4 2025 historical goals (emp_1) ────────────────────
            Goal(
                id="goal_hist_4", employee_id="emp_1",
                department_id="dep_hr", position="HR Business Partner",
                title="До 31.12 довести долю целей с привязкой к KPI до 80%",
                goal_text="До 31.12 довести долю целей с привязкой к KPI до 80%",
                metric="доля целей с привязкой к KPI >= 80%",
                deadline=date(2025, 12, 31),
                quarter="Q4", year=2025, weight=50.0, status="approved",
            ),
            Goal(
                id="goal_hist_5", employee_id="emp_1",
                department_id="dep_hr", position="HR Business Partner",
                title="До конца Q4 сократить среднее время согласования документов с 7 до 4 дней",
                goal_text="До конца Q4 сократить среднее время согласования документов с 7 до 4 дней",
                metric="среднее время согласования <= 4 дней",
                deadline=date(2025, 12, 31),
                quarter="Q4", year=2025, weight=50.0, status="approved",
            ),
            # ── Q1 2026 historical goals (emp_2 — L&D Specialist) ───
            Goal(
                id="goal_hist_6", employee_id="emp_2",
                department_id="dep_lnd", position="Learning and Development Specialist",
                title="До 31.03 обновить программу адаптации новых сотрудников и провести пилот в 2 подразделениях",
                goal_text="До 31.03 обновить программу адаптации новых сотрудников и провести пилот в 2 подразделениях",
                metric="программа обновлена, пилот в 2 подразделениях",
                deadline=date(2026, 3, 31),
                quarter="Q1", year=2026, weight=50.0, status="approved",
            ),
            Goal(
                id="goal_hist_7", employee_id="emp_2",
                department_id="dep_lnd", position="Learning and Development Specialist",
                title="До конца Q1 снизить долю просроченных обучений ниже 5% за счет автоматизации напоминаний",
                goal_text="До конца Q1 снизить долю просроченных обучений ниже 5% за счет автоматизации напоминаний",
                metric="доля просроченных обучений < 5%",
                deadline=date(2026, 3, 31),
                quarter="Q1", year=2026, weight=50.0, status="approved",
            ),
            # ── Manager goals (emp_mgr) ─────────────────────────────
            Goal(
                id="goal_mgr_1", employee_id="emp_mgr",
                department_id="dep_hr", position="Production Manager",
                title="До 30.06 сократить время внутренних HR-процессов на 20% за счет цифровизации и автоматизации",
                goal_text="До 30.06 сократить время внутренних HR-процессов на 20% за счет цифровизации и автоматизации",
                metric="сокращение времени HR-процессов на 20%",
                deadline=date(2026, 6, 30),
                quarter="Q2", year=2026, weight=40.0,
            ),
            Goal(
                id="goal_mgr_2", employee_id="emp_mgr",
                department_id="dep_hr", position="Production Manager",
                title="До конца Q2 повысить прозрачность исполнения обязательного обучения: 100% сотрудников в дашборде",
                goal_text="До конца Q2 повысить прозрачность исполнения обязательного обучения: 100% сотрудников в дашборде",
                metric="100% сотрудников в дашборде обучения",
                deadline=date(2026, 6, 30),
                quarter="Q2", year=2026, weight=30.0,
            ),
            Goal(
                id="goal_mgr_3", employee_id="emp_mgr",
                department_id="dep_hr", position="Production Manager",
                title="До 30.06 обеспечить рост доли стратегически связанных целей подчинённых не ниже 75%",
                goal_text="До 30.06 обеспечить рост доли стратегически связанных целей подчинённых не ниже 75%",
                metric="доля стратегически связанных целей >= 75%",
                deadline=date(2026, 6, 30),
                quarter="Q2", year=2026, weight=30.0,
            ),
            # ── Additional employees goals for richer demo ──────────
            Goal(
                id="goal_comp_1", employee_id="emp_3",
                department_id="dep_comp", position="Compensation and Benefits Specialist",
                title="До 30.06 провести анализ рынка заработных плат по 5 ключевым должностям и подготовить отчёт с рекомендациями",
                goal_text="До 30.06 провести анализ рынка заработных плат по 5 ключевым должностям и подготовить отчёт с рекомендациями",
                metric="анализ по 5 должностям + отчёт",
                deadline=date(2026, 6, 30),
                quarter="Q2", year=2026, weight=40.0,
            ),
            Goal(
                id="goal_comp_2", employee_id="emp_3",
                department_id="dep_comp", position="Compensation and Benefits Specialist",
                title="До конца Q2 обновить политику компенсаций и льгот с учётом анализа рынка и утвердить у руководства",
                goal_text="До конца Q2 обновить политику компенсаций и льгот с учётом анализа рынка и утвердить у руководства",
                metric="политика обновлена и утверждена",
                deadline=date(2026, 6, 30),
                quarter="Q2", year=2026, weight=30.0,
            ),
            Goal(
                id="goal_comp_3", employee_id="emp_3",
                department_id="dep_comp", position="Compensation and Benefits Specialist",
                title="До 30.06 снизить долю ошибок в расчёте бонусов ниже 2% за счет автоматизации проверки данных",
                goal_text="До 30.06 снизить долю ошибок в расчёте бонусов ниже 2% за счет автоматизации проверки данных",
                metric="доля ошибок в расчёте бонусов < 2%",
                deadline=date(2026, 6, 30),
                quarter="Q2", year=2026, weight=30.0,
            ),
            Goal(
                id="goal_rec_1", employee_id="emp_4",
                department_id="dep_rec", position="Recruiter",
                title="До 30.06 сократить средний срок закрытия вакансий с 45 до 30 рабочих дней за счет оптимизации воронки подбора",
                goal_text="До 30.06 сократить средний срок закрытия вакансий с 45 до 30 рабочих дней за счет оптимизации воронки подбора",
                metric="средний срок закрытия вакансий <= 30 дней",
                deadline=date(2026, 6, 30),
                quarter="Q2", year=2026, weight=40.0,
            ),
            Goal(
                id="goal_rec_2", employee_id="emp_4",
                department_id="dep_rec", position="Recruiter",
                title="До конца Q2 обеспечить укомплектованность критических позиций не ниже 95%",
                goal_text="До конца Q2 обеспечить укомплектованность критических позиций не ниже 95%",
                metric="укомплектованность критических позиций >= 95%",
                deadline=date(2026, 6, 30),
                quarter="Q2", year=2026, weight=35.0,
            ),
            Goal(
                id="goal_rec_3", employee_id="emp_4",
                department_id="dep_rec", position="Recruiter",
                title="До 30.06 внедрить систему реферальной программы и привлечь не менее 10 кандидатов через рекомендации сотрудников",
                goal_text="До 30.06 внедрить систему реферальной программы и привлечь не менее 10 кандидатов через рекомендации сотрудников",
                metric="реферальная программа запущена, >= 10 кандидатов",
                deadline=date(2026, 6, 30),
                quarter="Q2", year=2026, weight=25.0,
            ),
        ]

    # ── Accessors ────────────────────────────────────────────────────

    def get_employee(self, employee_id: str) -> Optional[Employee]:
        return self.employees.get(employee_id)

    def get_department(self, department_id: str) -> Optional[Department]:
        return self.departments.get(department_id)

    def get_position(self, position_id: str) -> Optional[Position]:
        return self.positions.get(position_id)

    def list_documents(self) -> list[Document]:
        return [d for d in self._documents.values() if d.is_active]

    def list_employee_goals(self, employee_id: str, quarter: str, year: int) -> list[Goal]:
        return [
            g for g in self._goals
            if g.employee_id == employee_id and g.quarter == quarter and g.year == year
        ]

    def add_documents(self, documents) -> int:
        for doc in documents:
            if isinstance(doc, dict):
                doc = Document(**doc)
            self._documents[doc.doc_id] = doc
        return len(documents)

    def list_departments(self) -> list[Department]:
        return list(self.departments.values())

    def list_employees(self, department_id: Optional[str] = None) -> list[Employee]:
        emps = list(self.employees.values())
        if department_id:
            emps = [e for e in emps if e.department_id == department_id]
        return emps

    def list_subordinates(self, manager_id: str) -> list[Employee]:
        return [e for e in self.employees.values() if e.manager_id == manager_id]

    def list_department_goals(self, department_id: str, quarter: Optional[str] = None, year: Optional[int] = None) -> list[Goal]:
        emp_ids = {e.id for e in self.employees.values() if e.department_id == department_id}
        goals = [g for g in self._goals if g.employee_id in emp_ids]
        if quarter:
            goals = [g for g in goals if g.quarter == quarter]
        if year:
            goals = [g for g in goals if g.year == year]
        return goals

    def list_all_goals_for_position(self, position_id: str, exclude_quarter: Optional[str] = None, exclude_year: Optional[int] = None) -> list[Goal]:
        """Return historical goals for employees in the same position (for achievability check)."""
        emp_ids = {e.id for e in self.employees.values() if e.position_id == position_id}
        goals = [g for g in self._goals if g.employee_id in emp_ids]
        if exclude_quarter and exclude_year:
            goals = [g for g in goals if not (g.quarter == exclude_quarter and g.year == exclude_year)]
        return goals

    def list_all_goals_for_department(self, department_id: str, exclude_quarter: Optional[str] = None, exclude_year: Optional[int] = None) -> list[Goal]:
        """Return historical goals for the department (for achievability check)."""
        emp_ids = {e.id for e in self.employees.values() if e.department_id == department_id}
        goals = [g for g in self._goals if g.employee_id in emp_ids]
        if exclude_quarter and exclude_year:
            goals = [g for g in goals if not (g.quarter == exclude_quarter and g.year == exclude_year)]
        return goals

    # ── §4.2 Extended table queries ──────────────────────────────────

    def list_goal_events(self, goal_id: str) -> list[GoalEvent]:
        """Return goal_events for a specific goal (F-15 versioning)."""
        return [e for e in self._goal_events if e.goal_id == goal_id]

    def list_goal_reviews(self, goal_id: str) -> list[GoalReview]:
        """Return goal_reviews for a specific goal."""
        return [r for r in self._goal_reviews if r.goal_id == goal_id]

    def get_kpi_for_department(self, department_id: str) -> list[KpiCatalog]:
        """Return KPI catalog items that have timeseries data for this department."""
        kpi_ids = {ts.kpi_id for ts in self._kpi_timeseries if ts.department_id == department_id}
        return [self._kpi_catalog[k] for k in kpi_ids if k in self._kpi_catalog]

    def get_kpi_timeseries(self, kpi_id: str, department_id: str) -> list[KpiTimeseries]:
        """Return timeseries values for a specific KPI in a department."""
        return [ts for ts in self._kpi_timeseries if ts.kpi_id == kpi_id and ts.department_id == department_id]

    def get_employee_projects(self, employee_id: str) -> list[dict]:
        """Return projects the employee is involved in."""
        return [ep for ep in self._employee_projects if ep.get("employee_id") == employee_id]

    def get_goal_history_stats(self, employee_id: str) -> dict:
        """Return aggregated goal history: how many goals approved/rejected/drafted."""
        stats: dict[str, int] = {}
        for g in self._goals:
            if g.employee_id == employee_id:
                stats[g.status] = stats.get(g.status, 0) + 1
        return stats

    def count_table_rows(self, table_name: str) -> int:
        """Return row count for a given logical table."""
        mapping = {
            "departments": len(self.departments),
            "positions": len(self.positions),
            "employees": len(self.employees),
            "documents": len(self._documents),
            "goals": len(self._goals),
            "goal_events": len(self._goal_events),
            "goal_reviews": len(self._goal_reviews),
            "kpi_catalog": len(self._kpi_catalog),
            "kpi_timeseries": len(self._kpi_timeseries),
            "projects": len(getattr(self, "_projects", {})),
            "systems": len(getattr(self, "_systems", {})),
            "project_systems": len(getattr(self, "_project_systems", [])),
            "employee_projects": len(self._employee_projects),
        }
        return mapping.get(table_name, 0)

    def has_dump_data(self) -> bool:
        """Check if we have significant data loaded (from organizer dump)."""
        return len(self.employees) > 50

    # ── Dump loader ──────────────────────────────────────────────────

    def load_synthetic_dump(self, dump_path: str | Path) -> dict[str, int]:
        """Load a synthetic §4.2 JSON dump into memory, replacing demo seed data."""
        dump_path = Path(dump_path)
        data = json.loads(dump_path.read_text(encoding="utf-8"))

        # Clear existing data
        self.departments.clear()
        self.positions.clear()
        self.employees.clear()
        self._documents.clear()
        self._goals.clear()
        self._goal_events.clear()
        self._goal_reviews.clear()
        self._kpi_catalog.clear()
        self._kpi_timeseries.clear()
        self._employee_projects.clear()
        self._projects: dict[str, dict] = {}
        self._systems: dict[str, dict] = {}
        self._project_systems: list[dict] = []

        # Load departments
        for d in data.get("departments", []):
            self.departments[d["id"]] = Department(**d)

        # Load positions
        for p in data.get("positions", []):
            self.positions[p["id"]] = Position(**p)

        # Load employees
        for e in data.get("employees", []):
            self.employees[e["id"]] = Employee(**e)

        # Load documents
        for doc in data.get("documents", []):
            self._documents[doc["doc_id"]] = Document(**doc)

        # Load goals
        for g in data.get("goals", []):
            self._goals.append(Goal(**g))

        # Load projects
        for p in data.get("projects", []):
            self._projects[p["id"]] = p

        # Load systems
        for s in data.get("systems", []):
            self._systems[s["id"]] = s

        # Load project_systems
        self._project_systems = data.get("project_systems", [])

        # Load employee_projects
        self._employee_projects = data.get("employee_projects", [])

        # Load goal_events
        for evt in data.get("goal_events", []):
            self._goal_events.append(GoalEvent(**evt))

        # Load goal_reviews
        for rev in data.get("goal_reviews", []):
            self._goal_reviews.append(GoalReview(**rev))

        # Load KPI catalog
        for kpi in data.get("kpi_catalog", []):
            self._kpi_catalog[kpi["id"]] = KpiCatalog(**kpi)

        # Load KPI timeseries
        for ts in data.get("kpi_timeseries", []):
            self._kpi_timeseries.append(KpiTimeseries(**ts))

        stats = {
            "departments": len(self.departments),
            "positions": len(self.positions),
            "employees": len(self.employees),
            "documents": len(self._documents),
            "goals": len(self._goals),
            "projects": len(self._projects),
            "systems": len(self._systems),
            "project_systems": len(self._project_systems),
            "employee_projects": len(self._employee_projects),
            "goal_events": len(self._goal_events),
            "goal_reviews": len(self._goal_reviews),
            "kpi_catalog": len(self._kpi_catalog),
            "kpi_timeseries": len(self._kpi_timeseries),
        }
        return stats
