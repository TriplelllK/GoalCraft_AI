from __future__ import annotations

from datetime import date
from typing import Any, Iterable, Optional
import time

from app.models.schemas import (
    Department, Document, Employee, Goal, Position,
    Project, System, EmployeeProject, GoalEvent, GoalReview,
    KpiCatalog, KpiTimeseries,
)


class PostgresStore:
    """PostgreSQL-backed repository for the hackathon schema.

    The class lazily imports psycopg so the project stays importable in restricted
    environments. In real runs, install `psycopg[binary]` and pass DATABASE_URL.
    """

    def __init__(self, database_url: str, auto_init: bool = True) -> None:
        if not database_url:
            raise ValueError("DATABASE_URL is required for PostgresStore")
        self.database_url = database_url
        self._psycopg = self._import_psycopg()
        self._ensure_connection_ready()
        if auto_init:
            self.ensure_schema_and_seed_demo_data()

    @staticmethod
    def _import_psycopg():
        try:
            import psycopg
        except Exception as exc:  # pragma: no cover - depends on environment
            raise RuntimeError(
                "psycopg is not installed. Install requirements and run again."
            ) from exc
        return psycopg

    def _connect(self):
        return self._psycopg.connect(self.database_url)


    def _ensure_connection_ready(self, retries: int = 20, delay: float = 1.0) -> None:
        last_error: Exception | None = None
        for _ in range(retries):
            try:
                with self._connect() as conn, conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
                    return
            except Exception as exc:  # pragma: no cover - external service timing
                last_error = exc
                time.sleep(delay)
        raise RuntimeError(f"Failed to connect to PostgreSQL: {last_error}")

    def ping(self) -> dict[str, Any]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            return {"backend": "postgres", "ok": cur.fetchone()[0] == 1}

    def ensure_schema_and_seed_demo_data(self) -> None:
        schema_sql = """
        -- ── Core tables (§2.1, §2.2) ────────────────────────────────
        CREATE TABLE IF NOT EXISTS departments (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            code TEXT NOT NULL,
            parent_id TEXT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS positions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            grade TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS employees (
            id TEXT PRIMARY KEY,
            employee_code TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            department_id TEXT NOT NULL REFERENCES departments(id),
            position_id TEXT NOT NULL REFERENCES positions(id),
            manager_id TEXT NULL,
            hire_date DATE NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS documents (
            doc_id TEXT PRIMARY KEY,
            doc_type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            valid_from DATE NULL,
            valid_to DATE NULL,
            owner_department_id TEXT NULL,
            department_scope TEXT[] NOT NULL DEFAULT '{}',
            keywords TEXT[] NOT NULL DEFAULT '{}',
            version TEXT NOT NULL DEFAULT '1.0',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS goals (
            id TEXT PRIMARY KEY,
            employee_id TEXT NOT NULL REFERENCES employees(id),
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'draft',
            quarter TEXT NOT NULL,
            year INTEGER NOT NULL,
            weight DOUBLE PRECISION NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );

        -- ── §4.2 Extended tables (hackathon dump) ───────────────────
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            start_date DATE NULL,
            end_date DATE NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS systems (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            system_type TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS project_systems (
            project_id TEXT NOT NULL REFERENCES projects(id),
            system_id TEXT NOT NULL REFERENCES systems(id),
            PRIMARY KEY (project_id, system_id)
        );

        CREATE TABLE IF NOT EXISTS employee_projects (
            employee_id TEXT NOT NULL REFERENCES employees(id),
            project_id TEXT NOT NULL REFERENCES projects(id),
            role TEXT NOT NULL DEFAULT '',
            allocation_percent DOUBLE PRECISION NOT NULL DEFAULT 0,
            start_date DATE NULL,
            end_date DATE NULL
        );

        CREATE TABLE IF NOT EXISTS goal_events (
            id TEXT PRIMARY KEY,
            goal_id TEXT NOT NULL REFERENCES goals(id),
            event_type TEXT NOT NULL DEFAULT '',
            actor_id TEXT NOT NULL DEFAULT '',
            old_status TEXT NOT NULL DEFAULT '',
            new_status TEXT NOT NULL DEFAULT '',
            old_text TEXT NOT NULL DEFAULT '',
            new_text TEXT NOT NULL DEFAULT '',
            metadata JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS goal_reviews (
            id TEXT PRIMARY KEY,
            goal_id TEXT NOT NULL REFERENCES goals(id),
            reviewer_id TEXT NOT NULL DEFAULT '',
            verdict TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS kpi_catalog (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            unit TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS kpi_timeseries (
            id TEXT PRIMARY KEY,
            kpi_id TEXT NOT NULL REFERENCES kpi_catalog(id),
            department_id TEXT NOT NULL DEFAULT '',
            period TEXT NOT NULL DEFAULT '',
            value DOUBLE PRECISION NOT NULL DEFAULT 0
        );
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(schema_sql)
            cur.execute("SELECT COUNT(*) FROM departments")
            count = cur.fetchone()[0]
            if count == 0:
                self._seed_demo(cur)
            conn.commit()

    def _seed_demo(self, cur) -> None:
        cur.executemany(
            "INSERT INTO departments (id, name, code) VALUES (%s, %s, %s)",
            [
                ("dep_hr", "HR / Production Block", "HR-PB"),
                ("dep_lnd", "Learning & Development", "LND"),
                ("dep_ops", "Production Operations", "OPS"),
            ],
        )
        cur.executemany(
            "INSERT INTO positions (id, name, grade) VALUES (%s, %s, %s)",
            [
                ("pos_hrbp", "HR Business Partner", "G10"),
                ("pos_lnd", "Learning and Development Specialist", "G9"),
                ("pos_mgr", "Production Manager", "G12"),
            ],
        )
        cur.executemany(
            """
            INSERT INTO employees (id, employee_code, full_name, email, department_id, position_id, manager_id, hire_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                ("emp_mgr", "E0001", "Aidos S.", "aidos@example.com", "dep_hr", "pos_mgr", None, date(2023, 1, 10)),
                ("emp_1", "E0002", "Aigerim S.", "aigerim@example.com", "dep_hr", "pos_hrbp", "emp_mgr", date(2024, 2, 1)),
                ("emp_2", "E0003", "Dana M.", "dana@example.com", "dep_lnd", "pos_lnd", "emp_mgr", date(2024, 3, 12)),
            ],
        )
        cur.executemany(
            """
            INSERT INTO documents (doc_id, doc_type, title, content, owner_department_id, department_scope, keywords, version, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (doc_id) DO NOTHING
            """,
            [
                (
                    "DOC-01", "strategy", "Программа снижения операционных затрат",
                    "Снизить удельные операционные затраты по производственным процессам за счет оптимизации планирования и цифровизации. Приоритет квартала — сокращение времени внутренних согласований и повышение прозрачности исполнения.",
                    "dep_ops", ["dep_hr", "dep_ops"], ["снижение затрат", "цифровизация", "согласование"], "1.0", True,
                ),
                (
                    "DOC-02", "vnd", "ВНД по развитию компетенций и обязательного обучения",
                    "Обеспечить своевременное прохождение обязательного обучения и развитие критически значимых компетенций сотрудников. Снизить долю просроченных обучений и автоматизировать напоминания.",
                    "dep_lnd", ["dep_hr", "dep_lnd", "dep_ops"], ["обучение", "компетенции", "напоминания"], "1.0", True,
                ),
                (
                    "DOC-03", "strategy", "Стратегия цифровизации производственных функций",
                    "Приоритет квартала — перевод ручных процессов в цифровой формат и повышение прозрачности исполнения задач. Требуется сократить срок внутренних HR-процессов и повысить управляемость статусов.",
                    "dep_hr", ["dep_hr", "dep_ops"], ["цифровизация", "HR", "прозрачность"], "1.0", True,
                ),
                (
                    "DOC-04", "kpi", "KPI каталога HR-подразделения",
                    "Ключевые KPI подразделения: доля целей, привязанных к KPI, средний срок согласования HR-заявок, доля обязательного обучения, доля стратегически связанных целей.",
                    "dep_hr", ["dep_hr"], ["KPI", "HR-заявки", "цели"], "1.0", True,
                ),
                (
                    "DOC-05", "manager_goal", "Цель руководителя на квартал",
                    "Сократить время внутренних HR-процессов и повысить прозрачность исполнения по обязательному обучению. Обеспечить рост стратегической связки целей сотрудников в производственном блоке.",
                    "dep_hr", ["dep_hr"], ["руководитель", "прозрачность", "обучение"], "1.0", True,
                ),
            ],
        )
        cur.executemany(
            """
            INSERT INTO goals (id, employee_id, title, quarter, year, weight)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            [
                ("goal_demo_1", "emp_1", "До конца Q2 довести долю целей, привязанных к KPI подразделения, до 85%", "Q2", 2026, 50.0),
                ("goal_demo_2", "emp_1", "До 30.06 сократить средний срок согласования HR-заявок с 5 до 3 рабочих дней", "Q2", 2026, 50.0),
            ],
        )

    @staticmethod
    def _row_to_department(row) -> Department:
        return Department(id=row[0], name=row[1], code=row[2], parent_id=row[3], is_active=row[4])

    @staticmethod
    def _row_to_position(row) -> Position:
        return Position(id=row[0], name=row[1], grade=row[2])

    @staticmethod
    def _row_to_employee(row) -> Employee:
        return Employee(
            id=row[0],
            employee_code=row[1],
            full_name=row[2],
            email=row[3],
            department_id=row[4],
            position_id=row[5],
            manager_id=row[6],
            hire_date=row[7],
            is_active=row[8],
        )

    @staticmethod
    def _row_to_document(row) -> Document:
        return Document(
            doc_id=row[0],
            doc_type=row[1],
            title=row[2],
            content=row[3],
            valid_from=row[4],
            valid_to=row[5],
            owner_department_id=row[6],
            department_scope=list(row[7] or []),
            keywords=list(row[8] or []),
            version=row[9],
            is_active=row[10],
        )

    @staticmethod
    def _row_to_goal(row) -> Goal:
        return Goal(
            id=row[0],
            employee_id=row[1],
            title=row[2],
            description=row[3],
            status=row[4],
            quarter=row[5],
            year=row[6],
            weight=row[7],
            created_at=row[8].isoformat() if row[8] else '',
            updated_at=row[9].isoformat() if row[9] else '',
        )

    def get_employee(self, employee_id: str) -> Optional[Employee]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id, employee_code, full_name, email, department_id, position_id, manager_id, hire_date, is_active FROM employees WHERE id = %s",
                (employee_id,),
            )
            row = cur.fetchone()
            return self._row_to_employee(row) if row else None

    def get_department(self, department_id: str) -> Optional[Department]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT id, name, code, parent_id, is_active FROM departments WHERE id = %s", (department_id,))
            row = cur.fetchone()
            return self._row_to_department(row) if row else None

    def get_position(self, position_id: str) -> Optional[Position]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT id, name, grade FROM positions WHERE id = %s", (position_id,))
            row = cur.fetchone()
            return self._row_to_position(row) if row else None

    def list_employee_goals(self, employee_id: str, quarter: str, year: int) -> list[Goal]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, employee_id, title, COALESCE(description, ''), status, quarter, year, weight, created_at, updated_at
                FROM goals WHERE employee_id = %s AND quarter = %s AND year = %s
                ORDER BY created_at
                """,
                (employee_id, quarter, year),
            )
            return [self._row_to_goal(row) for row in cur.fetchall()]

    def add_documents(self, documents: list[Document]) -> int:
        with self._connect() as conn, conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO documents (doc_id, doc_type, title, content, valid_from, valid_to, owner_department_id, department_scope, keywords, version, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (doc_id) DO UPDATE SET
                    doc_type = EXCLUDED.doc_type,
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    valid_from = EXCLUDED.valid_from,
                    valid_to = EXCLUDED.valid_to,
                    owner_department_id = EXCLUDED.owner_department_id,
                    department_scope = EXCLUDED.department_scope,
                    keywords = EXCLUDED.keywords,
                    version = EXCLUDED.version,
                    is_active = EXCLUDED.is_active,
                    updated_at = NOW()
                """,
                [
                    (
                        item.doc_id,
                        item.doc_type,
                        item.title,
                        item.content,
                        item.valid_from,
                        item.valid_to,
                        item.owner_department_id,
                        item.department_scope,
                        item.keywords,
                        item.version,
                        item.is_active,
                    )
                    for item in documents
                ],
            )
            conn.commit()
        return len(documents)

    def list_documents(self) -> list[Document]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT doc_id, doc_type, title, content, valid_from, valid_to, owner_department_id, department_scope, keywords, version, is_active
                FROM documents WHERE is_active = TRUE ORDER BY doc_id
                """
            )
            return [self._row_to_document(row) for row in cur.fetchall()]

    def list_departments(self) -> list[Department]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT id, name, code, parent_id, is_active FROM departments WHERE is_active = TRUE ORDER BY name")
            return [self._row_to_department(row) for row in cur.fetchall()]

    def list_employees(self, department_id: Optional[str] = None) -> list[Employee]:
        sql = "SELECT id, employee_code, full_name, email, department_id, position_id, manager_id, hire_date, is_active FROM employees WHERE is_active = TRUE"
        params: Iterable[Any] = ()
        if department_id:
            sql += " AND department_id = %s"
            params = (department_id,)
        sql += " ORDER BY full_name"
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            return [self._row_to_employee(row) for row in cur.fetchall()]

    # ── Dict-like properties for engine compatibility ────────────────

    @property
    def employees(self) -> dict[str, Employee]:
        return {e.id: e for e in self.list_employees()}

    @property
    def departments(self) -> dict[str, Department]:
        return {d.id: d for d in self.list_departments()}

    def list_subordinates(self, manager_id: str) -> list[Employee]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id, employee_code, full_name, email, department_id, position_id, manager_id, hire_date, is_active "
                "FROM employees WHERE manager_id = %s AND is_active = TRUE ORDER BY full_name",
                (manager_id,),
            )
            return [self._row_to_employee(row) for row in cur.fetchall()]

    def list_department_goals(self, department_id: str, quarter: Optional[str] = None, year: Optional[int] = None) -> list[Goal]:
        sql = """
            SELECT g.id, g.employee_id, g.title, COALESCE(g.description,''), g.status, g.quarter, g.year, g.weight, g.created_at, g.updated_at
            FROM goals g JOIN employees e ON g.employee_id = e.id
            WHERE e.department_id = %s
        """
        params: list[Any] = [department_id]
        if quarter:
            sql += " AND g.quarter = %s"
            params.append(quarter)
        if year:
            sql += " AND g.year = %s"
            params.append(year)
        sql += " ORDER BY g.created_at"
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            return [self._row_to_goal(row) for row in cur.fetchall()]

    def list_all_goals_for_position(self, position_id: str, exclude_quarter: Optional[str] = None, exclude_year: Optional[int] = None) -> list[Goal]:
        sql = """
            SELECT g.id, g.employee_id, g.title, COALESCE(g.description,''), g.status, g.quarter, g.year, g.weight, g.created_at, g.updated_at
            FROM goals g JOIN employees e ON g.employee_id = e.id
            WHERE e.position_id = %s
        """
        params: list[Any] = [position_id]
        if exclude_quarter and exclude_year:
            sql += " AND NOT (g.quarter = %s AND g.year = %s)"
            params.extend([exclude_quarter, exclude_year])
        sql += " ORDER BY g.created_at"
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            return [self._row_to_goal(row) for row in cur.fetchall()]

    def list_all_goals_for_department(self, department_id: str, exclude_quarter: Optional[str] = None, exclude_year: Optional[int] = None) -> list[Goal]:
        sql = """
            SELECT g.id, g.employee_id, g.title, COALESCE(g.description,''), g.status, g.quarter, g.year, g.weight, g.created_at, g.updated_at
            FROM goals g JOIN employees e ON g.employee_id = e.id
            WHERE e.department_id = %s
        """
        params: list[Any] = [department_id]
        if exclude_quarter and exclude_year:
            sql += " AND NOT (g.quarter = %s AND g.year = %s)"
            params.extend([exclude_quarter, exclude_year])
        sql += " ORDER BY g.created_at"
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            return [self._row_to_goal(row) for row in cur.fetchall()]

    # ── §4.2 Extended table queries ──────────────────────────────────

    def list_goal_events(self, goal_id: str) -> list:
        """Return goal_events for a specific goal (F-15 versioning)."""
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id, goal_id, event_type, actor_id, old_status, new_status, old_text, new_text, metadata::text, created_at "
                "FROM goal_events WHERE goal_id = %s ORDER BY created_at",
                (goal_id,),
            )
            return [
                GoalEvent(
                    id=r[0], goal_id=r[1], event_type=r[2], actor_id=r[3],
                    old_status=r[4], new_status=r[5], old_text=r[6], new_text=r[7],
                    metadata=r[8] or "", created_at=r[9].isoformat() if r[9] else "",
                )
                for r in cur.fetchall()
            ]

    def list_goal_reviews(self, goal_id: str) -> list:
        """Return goal_reviews for a specific goal."""
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id, goal_id, reviewer_id, verdict, created_at "
                "FROM goal_reviews WHERE goal_id = %s ORDER BY created_at",
                (goal_id,),
            )
            return [
                GoalReview(
                    id=r[0], goal_id=r[1], reviewer_id=r[2], verdict=r[3],
                    created_at=r[4].isoformat() if r[4] else "",
                )
                for r in cur.fetchall()
            ]

    def get_kpi_for_department(self, department_id: str) -> list:
        """Return KPI catalog items that have timeseries data for this department."""
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT k.id, k.name, k.unit, k.description
                FROM kpi_catalog k
                JOIN kpi_timeseries ts ON k.id = ts.kpi_id
                WHERE ts.department_id = %s
                ORDER BY k.name
                """,
                (department_id,),
            )
            return [
                KpiCatalog(id=r[0], name=r[1], unit=r[2], description=r[3])
                for r in cur.fetchall()
            ]

    def get_kpi_timeseries(self, kpi_id: str, department_id: str) -> list:
        """Return timeseries values for a specific KPI in a department."""
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id, kpi_id, department_id, period, value "
                "FROM kpi_timeseries WHERE kpi_id = %s AND department_id = %s ORDER BY period",
                (kpi_id, department_id),
            )
            return [
                KpiTimeseries(id=r[0], kpi_id=r[1], department_id=r[2], period=r[3], value=r[4])
                for r in cur.fetchall()
            ]

    def get_employee_projects(self, employee_id: str) -> list:
        """Return projects the employee is involved in."""
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT ep.employee_id, ep.project_id, ep.role, ep.allocation_percent, ep.start_date, ep.end_date,
                       p.name as project_name, p.status as project_status
                FROM employee_projects ep
                JOIN projects p ON ep.project_id = p.id
                WHERE ep.employee_id = %s
                ORDER BY p.name
                """,
                (employee_id,),
            )
            return [
                {
                    "project_id": r[1], "role": r[2], "allocation_percent": r[3],
                    "project_name": r[6], "project_status": r[7],
                }
                for r in cur.fetchall()
            ]

    def get_goal_history_stats(self, employee_id: str) -> dict:
        """Return aggregated goal history: how many goals approved/rejected/drafted."""
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT status, COUNT(*) FROM goals WHERE employee_id = %s GROUP BY status",
                (employee_id,),
            )
            return dict(cur.fetchall())

    def count_table_rows(self, table_name: str) -> int:
        """Return row count for any table (used for health check)."""
        allowed = {
            "departments", "positions", "employees", "documents", "goals",
            "projects", "systems", "project_systems", "employee_projects",
            "goal_events", "goal_reviews", "kpi_catalog", "kpi_timeseries",
        }
        if table_name not in allowed:
            return 0
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")  # noqa: S608 — table name is validated above
            return cur.fetchone()[0]

    def has_dump_data(self) -> bool:
        """Check if the database has data from the organizer's dump (>100 employees)."""
        try:
            return self.count_table_rows("employees") > 50
        except Exception:
            return False
