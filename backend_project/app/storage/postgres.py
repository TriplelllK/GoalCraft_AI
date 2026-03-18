from __future__ import annotations

import json
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

    Supports TWO schema variants:
      1. **Demo schema** — created by ensure_schema_and_seed_demo_data() with TEXT PKs.
      2. **Dump schema (§4.2)** — loaded by pg_restore from the hackathon PGDMP file
         with bigint / uuid PKs, PostgreSQL enums, and JSONB columns.

    Schema detection is automatic: if `goals.goal_id` column exists → dump schema.
    """

    def __init__(self, database_url: str, auto_init: bool = True) -> None:
        if not database_url:
            raise ValueError("DATABASE_URL is required for PostgresStore")
        self.database_url = database_url
        self._psycopg = self._import_psycopg()
        self._ensure_connection_ready()
        self._is_dump_schema = False
        if auto_init:
            self._detect_and_init_schema()

    # ── Infrastructure ───────────────────────────────────────────────

    @staticmethod
    def _import_psycopg():
        try:
            import psycopg
        except Exception as exc:
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
            except Exception as exc:
                last_error = exc
                time.sleep(delay)
        raise RuntimeError(f"Failed to connect to PostgreSQL: {last_error}")

    def ping(self) -> dict[str, Any]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            return {"backend": "postgres", "ok": cur.fetchone()[0] == 1}

    # ── Schema detection ─────────────────────────────────────────────

    def _detect_and_init_schema(self) -> None:
        """Detect if the hackathon dump (§4.2) is already loaded.
        If yes — use the dump tables as-is.
        If no  — create demo schema and seed sample data.
        """
        with self._connect() as conn, conn.cursor() as cur:
            # Check if the goals table exists with the dump-specific column `goal_id`
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'goals'
                      AND column_name = 'goal_id'
                )
            """)
            self._is_dump_schema = cur.fetchone()[0]

        if self._is_dump_schema:
            print("[PostgresStore] ✅ Hackathon dump schema detected (§4.2)")
        else:
            self.ensure_schema_and_seed_demo_data()

    # ── SQL helpers for schema-specific column names ─────────────────

    def _goal_select_cols(self) -> str:
        """Return SELECT columns for goals, always mapping to 16-column _row_to_goal order."""
        if self._is_dump_schema:
            return """
                g.goal_id::text,
                g.employee_id::text,
                g.department_id::text,
                COALESCE(g.position_snapshot, ''),
                g.goal_text,
                g.goal_text,
                '',
                COALESCE(g.metric, ''),
                g.deadline,
                g.status::text,
                g.quarter::text,
                g.year::int,
                g.weight::float,
                '',
                g.created_at,
                g.updated_at
            """
        return """
            g.id,
            g.employee_id,
            COALESCE(g.department_id, ''),
            COALESCE(g.position, ''),
            g.title,
            COALESCE(g.goal_text, ''),
            COALESCE(g.description, ''),
            COALESCE(g.metric, ''),
            g.deadline,
            g.status,
            g.quarter,
            g.year,
            g.weight,
            COALESCE(g.reviewer_comment, ''),
            g.created_at,
            g.updated_at
        """

    def _goal_id_col(self) -> str:
        return "g.goal_id" if self._is_dump_schema else "g.id"

    # ── Demo schema DDL + seed data ──────────────────────────────────

    def ensure_schema_and_seed_demo_data(self) -> None:
        schema_sql = """
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
            department_id TEXT NOT NULL DEFAULT '',
            position TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL,
            goal_text TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            metric TEXT NOT NULL DEFAULT '',
            deadline DATE NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            quarter TEXT NOT NULL,
            year INTEGER NOT NULL,
            weight DOUBLE PRECISION NULL,
            reviewer_comment TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
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
            comment_text TEXT NOT NULL DEFAULT '',
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
            """INSERT INTO employees (id, employee_code, full_name, email, department_id, position_id, manager_id, hire_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            [
                ("emp_mgr", "E0001", "Aidos S.", "aidos@example.com", "dep_hr", "pos_mgr", None, date(2023, 1, 10)),
                ("emp_1", "E0002", "Aigerim S.", "aigerim@example.com", "dep_hr", "pos_hrbp", "emp_mgr", date(2024, 2, 1)),
                ("emp_2", "E0003", "Dana M.", "dana@example.com", "dep_lnd", "pos_lnd", "emp_mgr", date(2024, 3, 12)),
            ],
        )
        cur.executemany(
            """INSERT INTO documents (doc_id, doc_type, title, content, owner_department_id, department_scope, keywords, version, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (doc_id) DO NOTHING""",
            [
                ("DOC-01", "strategy", "Программа снижения операционных затрат",
                 "Снизить удельные операционные затраты по производственным процессам за счет оптимизации планирования и цифровизации.",
                 "dep_ops", ["dep_hr", "dep_ops"], ["снижение затрат", "цифровизация"], "1.0", True),
                ("DOC-02", "vnd", "ВНД по развитию компетенций и обязательного обучения",
                 "Обеспечить своевременное прохождение обязательного обучения и развитие компетенций сотрудников.",
                 "dep_lnd", ["dep_hr", "dep_lnd", "dep_ops"], ["обучение", "компетенции"], "1.0", True),
                ("DOC-03", "strategy", "Стратегия цифровизации производственных функций",
                 "Приоритет квартала — перевод ручных процессов в цифровой формат и повышение прозрачности исполнения задач.",
                 "dep_hr", ["dep_hr", "dep_ops"], ["цифровизация", "HR", "прозрачность"], "1.0", True),
                ("DOC-04", "kpi", "KPI каталога HR-подразделения",
                 "Ключевые KPI подразделения: доля целей привязанных к KPI, средний срок согласования HR-заявок.",
                 "dep_hr", ["dep_hr"], ["KPI", "HR-заявки", "цели"], "1.0", True),
                ("DOC-05", "manager_goal", "Цель руководителя на квартал",
                 "Сократить время внутренних HR-процессов и повысить прозрачность исполнения по обязательному обучению.",
                 "dep_hr", ["dep_hr"], ["руководитель", "прозрачность", "обучение"], "1.0", True),
            ],
        )
        cur.executemany(
            """INSERT INTO goals (id, employee_id, department_id, position, title, goal_text, quarter, year, weight)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING""",
            [
                ("goal_demo_1", "emp_1", "dep_hr", "HR Business Partner",
                 "До конца Q2 довести долю целей, привязанных к KPI подразделения, до 85%",
                 "До конца Q2 довести долю целей, привязанных к KPI подразделения, до 85%",
                 "Q2", 2026, 50.0),
                ("goal_demo_2", "emp_1", "dep_hr", "HR Business Partner",
                 "До 30.06 сократить средний срок согласования HR-заявок с 5 до 3 рабочих дней",
                 "До 30.06 сократить средний срок согласования HR-заявок с 5 до 3 рабочих дней",
                 "Q2", 2026, 50.0),
            ],
        )

    # ── Row converters (handle both TEXT and bigint/uuid PKs) ────────

    @staticmethod
    def _row_to_department(row) -> Department:
        return Department(
            id=str(row[0]),
            name=str(row[1]),
            code=str(row[2] or ''),
            parent_id=str(row[3]) if row[3] is not None else None,
            is_active=bool(row[4]),
        )

    @staticmethod
    def _row_to_position(row) -> Position:
        return Position(id=str(row[0]), name=str(row[1]), grade=str(row[2] or ''))

    @staticmethod
    def _row_to_employee(row) -> Employee:
        return Employee(
            id=str(row[0]),
            employee_code=str(row[1] or ''),
            full_name=str(row[2]),
            email=str(row[3] or ''),
            department_id=str(row[4]),
            position_id=str(row[5]),
            manager_id=str(row[6]) if row[6] is not None else None,
            hire_date=row[7],
            is_active=bool(row[8]) if row[8] is not None else True,
        )

    @staticmethod
    def _row_to_document(row) -> Document:
        # department_scope can be TEXT[] (demo) or JSONB (dump)
        raw_scope = row[7]
        if raw_scope is None:
            scope = []
        elif isinstance(raw_scope, str):
            try:
                scope = json.loads(raw_scope) if raw_scope.startswith("[") else [raw_scope]
            except (json.JSONDecodeError, TypeError):
                scope = [raw_scope] if raw_scope else []
        elif isinstance(raw_scope, (list, tuple)):
            scope = [str(x) for x in raw_scope]
        else:
            scope = []

        # keywords can be TEXT[] or JSONB
        raw_kw = row[8]
        if raw_kw is None:
            keywords = []
        elif isinstance(raw_kw, (list, tuple)):
            keywords = [str(x) for x in raw_kw]
        elif isinstance(raw_kw, str):
            try:
                keywords = json.loads(raw_kw) if raw_kw.startswith("[") else [raw_kw]
            except (json.JSONDecodeError, TypeError):
                keywords = [raw_kw] if raw_kw else []
        else:
            keywords = []

        return Document(
            doc_id=str(row[0]),
            doc_type=str(row[1]),
            title=str(row[2]),
            content=str(row[3]),
            valid_from=row[4],
            valid_to=row[5],
            owner_department_id=str(row[6]) if row[6] is not None else None,
            department_scope=scope,
            keywords=keywords,
            version=str(row[9] or '1.0'),
            is_active=bool(row[10]) if row[10] is not None else True,
        )

    @staticmethod
    def _row_to_goal(row) -> Goal:
        """Convert a 16-column row to Goal (works for both demo and dump schemas)."""
        return Goal(
            id=str(row[0]),
            employee_id=str(row[1]),
            department_id=str(row[2] or ''),
            position=str(row[3] or ''),
            title=str(row[4] or ''),
            goal_text=str(row[5] or ''),
            description=str(row[6] or ''),
            metric=str(row[7] or ''),
            deadline=row[8],
            status=str(row[9] or 'draft'),
            quarter=str(row[10] or ''),
            year=int(row[11]) if row[11] else 0,
            weight=float(row[12]) if row[12] is not None else None,
            reviewer_comment=str(row[13] or ''),
            created_at=row[14].isoformat() if row[14] else '',
            updated_at=row[15].isoformat() if row[15] else '',
        )

    # ── Single-entity lookups ────────────────────────────────────────

    def get_employee(self, employee_id: str) -> Optional[Employee]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id, employee_code, full_name, email, department_id, "
                "position_id, manager_id, hire_date, is_active "
                "FROM employees WHERE id = %s",
                (employee_id,),
            )
            row = cur.fetchone()
            return self._row_to_employee(row) if row else None

    def get_department(self, department_id: str) -> Optional[Department]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, code, parent_id, is_active "
                "FROM departments WHERE id = %s",
                (department_id,),
            )
            row = cur.fetchone()
            return self._row_to_department(row) if row else None

    def get_position(self, position_id: str) -> Optional[Position]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT id, name, grade FROM positions WHERE id = %s", (position_id,))
            row = cur.fetchone()
            return self._row_to_position(row) if row else None

    # ── Goal queries ─────────────────────────────────────────────────

    def list_employee_goals(self, employee_id: str, quarter: str, year: int) -> list[Goal]:
        cols = self._goal_select_cols()
        with self._connect() as conn, conn.cursor() as cur:
            if self._is_dump_schema:
                cur.execute(
                    f"SELECT {cols} FROM goals g "
                    f"WHERE g.employee_id = %s::bigint AND g.quarter::text = %s AND g.year = %s "
                    f"ORDER BY g.created_at",
                    (employee_id, quarter, year),
                )
            else:
                cur.execute(
                    f"SELECT {cols} FROM goals g "
                    f"WHERE g.employee_id = %s AND g.quarter = %s AND g.year = %s "
                    f"ORDER BY g.created_at",
                    (employee_id, quarter, year),
                )
            return [self._row_to_goal(row) for row in cur.fetchall()]

    def list_department_goals(self, department_id: str, quarter: Optional[str] = None, year: Optional[int] = None) -> list[Goal]:
        cols = self._goal_select_cols()
        if self._is_dump_schema:
            sql = f"SELECT {cols} FROM goals g JOIN employees e ON g.employee_id = e.id WHERE e.department_id = %s::bigint"
        else:
            sql = f"SELECT {cols} FROM goals g JOIN employees e ON g.employee_id = e.id WHERE e.department_id = %s"
        params: list[Any] = [department_id]
        if quarter:
            if self._is_dump_schema:
                sql += " AND g.quarter::text = %s"
            else:
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
        cols = self._goal_select_cols()
        if self._is_dump_schema:
            sql = f"SELECT {cols} FROM goals g JOIN employees e ON g.employee_id = e.id WHERE e.position_id = %s::bigint"
        else:
            sql = f"SELECT {cols} FROM goals g JOIN employees e ON g.employee_id = e.id WHERE e.position_id = %s"
        params: list[Any] = [position_id]
        if exclude_quarter and exclude_year:
            if self._is_dump_schema:
                sql += " AND NOT (g.quarter::text = %s AND g.year = %s)"
            else:
                sql += " AND NOT (g.quarter = %s AND g.year = %s)"
            params.extend([exclude_quarter, exclude_year])
        sql += " ORDER BY g.created_at"
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            return [self._row_to_goal(row) for row in cur.fetchall()]

    def list_all_goals_for_department(self, department_id: str, exclude_quarter: Optional[str] = None, exclude_year: Optional[int] = None) -> list[Goal]:
        cols = self._goal_select_cols()
        if self._is_dump_schema:
            sql = f"SELECT {cols} FROM goals g JOIN employees e ON g.employee_id = e.id WHERE e.department_id = %s::bigint"
        else:
            sql = f"SELECT {cols} FROM goals g JOIN employees e ON g.employee_id = e.id WHERE e.department_id = %s"
        params: list[Any] = [department_id]
        if exclude_quarter and exclude_year:
            if self._is_dump_schema:
                sql += " AND NOT (g.quarter::text = %s AND g.year = %s)"
            else:
                sql += " AND NOT (g.quarter = %s AND g.year = %s)"
            params.extend([exclude_quarter, exclude_year])
        sql += " ORDER BY g.created_at"
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            return [self._row_to_goal(row) for row in cur.fetchall()]

    # ── Document operations ──────────────────────────────────────────

    def add_documents(self, documents: list[Document]) -> int:
        if self._is_dump_schema:
            # In dump schema, documents table has uuid PK and jsonb scope;
            # for user-ingested docs, generate uuid and convert scope to jsonb.
            with self._connect() as conn, conn.cursor() as cur:
                for item in documents:
                    scope_json = json.dumps(item.department_scope or [])
                    kw_array = item.keywords or []
                    cur.execute(
                        """
                        INSERT INTO documents (doc_id, doc_type, title, content, valid_from, valid_to,
                            owner_department_id, department_scope, keywords, version, is_active)
                        VALUES (gen_random_uuid(), %s::doc_type_enum, %s, %s, %s, %s,
                            %s::bigint, %s::jsonb, %s::text[], %s, %s)
                        """,
                        (item.doc_type, item.title, item.content,
                         item.valid_from, item.valid_to,
                         item.owner_department_id,
                         scope_json, kw_array,
                         item.version, item.is_active),
                    )
                conn.commit()
            return len(documents)

        # Demo schema — TEXT PKs
        with self._connect() as conn, conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO documents (doc_id, doc_type, title, content, valid_from, valid_to,
                    owner_department_id, department_scope, keywords, version, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (doc_id) DO UPDATE SET
                    doc_type = EXCLUDED.doc_type, title = EXCLUDED.title,
                    content = EXCLUDED.content, valid_from = EXCLUDED.valid_from,
                    valid_to = EXCLUDED.valid_to, owner_department_id = EXCLUDED.owner_department_id,
                    department_scope = EXCLUDED.department_scope, keywords = EXCLUDED.keywords,
                    version = EXCLUDED.version, is_active = EXCLUDED.is_active, updated_at = NOW()
                """,
                [(item.doc_id, item.doc_type, item.title, item.content,
                  item.valid_from, item.valid_to, item.owner_department_id,
                  item.department_scope, item.keywords, item.version, item.is_active)
                 for item in documents],
            )
            conn.commit()
        return len(documents)

    def list_documents(self) -> list[Document]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT doc_id, doc_type, title, content, valid_from, valid_to, "
                "owner_department_id, department_scope, keywords, version, is_active "
                "FROM documents WHERE is_active = TRUE ORDER BY doc_id"
            )
            return [self._row_to_document(row) for row in cur.fetchall()]

    # ── Reference lists (for UI dropdowns) ───────────────────────────

    def list_departments(self) -> list[Department]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, code, parent_id, is_active "
                "FROM departments WHERE is_active = TRUE ORDER BY name"
            )
            return [self._row_to_department(row) for row in cur.fetchall()]

    def list_employees(self, department_id: Optional[str] = None) -> list[Employee]:
        sql = ("SELECT id, employee_code, full_name, email, department_id, "
               "position_id, manager_id, hire_date, is_active "
               "FROM employees WHERE is_active = TRUE")
        params: Iterable[Any] = ()
        if department_id:
            if self._is_dump_schema:
                sql += " AND department_id = %s::bigint"
            else:
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
            if self._is_dump_schema:
                cur.execute(
                    "SELECT id, employee_code, full_name, email, department_id, "
                    "position_id, manager_id, hire_date, is_active "
                    "FROM employees WHERE manager_id = %s::bigint AND is_active = TRUE ORDER BY full_name",
                    (manager_id,),
                )
            else:
                cur.execute(
                    "SELECT id, employee_code, full_name, email, department_id, "
                    "position_id, manager_id, hire_date, is_active "
                    "FROM employees WHERE manager_id = %s AND is_active = TRUE ORDER BY full_name",
                    (manager_id,),
                )
            return [self._row_to_employee(row) for row in cur.fetchall()]

    # ── §4.2 Extended table queries ──────────────────────────────────

    def list_goal_events(self, goal_id: str) -> list:
        """Return goal_events for a specific goal (F-15 versioning)."""
        with self._connect() as conn, conn.cursor() as cur:
            if self._is_dump_schema:
                cur.execute(
                    "SELECT id::text, goal_id::text, event_type::text, "
                    "COALESCE(actor_id::text, ''), COALESCE(old_status::text, ''), "
                    "COALESCE(new_status::text, ''), COALESCE(old_text, ''), "
                    "COALESCE(new_text, ''), COALESCE(metadata::text, ''), created_at "
                    "FROM goal_events WHERE goal_id = %s::uuid ORDER BY created_at",
                    (goal_id,),
                )
            else:
                cur.execute(
                    "SELECT id, goal_id, event_type, actor_id, old_status, new_status, "
                    "old_text, new_text, metadata::text, created_at "
                    "FROM goal_events WHERE goal_id = %s ORDER BY created_at",
                    (goal_id,),
                )
            return [
                GoalEvent(
                    id=str(r[0]), goal_id=str(r[1]), event_type=str(r[2]),
                    actor_id=str(r[3]), old_status=str(r[4]), new_status=str(r[5]),
                    old_text=str(r[6]), new_text=str(r[7]),
                    metadata=str(r[8] or ""),
                    created_at=r[9].isoformat() if r[9] else "",
                )
                for r in cur.fetchall()
            ]

    def list_goal_reviews(self, goal_id: str) -> list:
        """Return goal_reviews for a specific goal."""
        with self._connect() as conn, conn.cursor() as cur:
            if self._is_dump_schema:
                cur.execute(
                    "SELECT id::text, goal_id::text, "
                    "COALESCE(reviewer_id::text, ''), verdict::text, "
                    "COALESCE(comment_text, ''), created_at "
                    "FROM goal_reviews WHERE goal_id = %s::uuid ORDER BY created_at",
                    (goal_id,),
                )
            else:
                cur.execute(
                    "SELECT id, goal_id, reviewer_id, verdict, "
                    "COALESCE(comment_text, ''), created_at "
                    "FROM goal_reviews WHERE goal_id = %s ORDER BY created_at",
                    (goal_id,),
                )
            return [
                GoalReview(
                    id=str(r[0]), goal_id=str(r[1]), reviewer_id=str(r[2]),
                    verdict=str(r[3]),
                    comment_text=str(r[4] or ''),
                    created_at=r[5].isoformat() if r[5] else "",
                )
                for r in cur.fetchall()
            ]

    def get_kpi_for_department(self, department_id: str) -> list:
        """Return KPI catalog items that have timeseries data for this department."""
        with self._connect() as conn, conn.cursor() as cur:
            if self._is_dump_schema:
                cur.execute(
                    """
                    SELECT DISTINCT k.metric_key, k.title, k.unit, COALESCE(k.description, '')
                    FROM kpi_catalog k
                    JOIN kpi_timeseries ts ON k.metric_key = ts.metric_key
                    WHERE ts.department_id = %s::bigint
                    ORDER BY k.title
                    """,
                    (department_id,),
                )
            else:
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
                KpiCatalog(id=str(r[0]), name=str(r[1]), unit=str(r[2]), description=str(r[3] or ''))
                for r in cur.fetchall()
            ]

    def get_kpi_timeseries(self, kpi_id: str, department_id: str) -> list:
        """Return timeseries values for a specific KPI in a department."""
        with self._connect() as conn, conn.cursor() as cur:
            if self._is_dump_schema:
                cur.execute(
                    "SELECT id::text, metric_key, department_id::text, "
                    "period_date::text, value_num::float "
                    "FROM kpi_timeseries "
                    "WHERE metric_key = %s AND department_id = %s::bigint "
                    "ORDER BY period_date",
                    (kpi_id, department_id),
                )
            else:
                cur.execute(
                    "SELECT id, kpi_id, department_id, period, value "
                    "FROM kpi_timeseries WHERE kpi_id = %s AND department_id = %s ORDER BY period",
                    (kpi_id, department_id),
                )
            return [
                KpiTimeseries(
                    id=str(r[0]), kpi_id=str(r[1]), department_id=str(r[2]),
                    period=str(r[3]), value=float(r[4]),
                )
                for r in cur.fetchall()
            ]

    def get_employee_projects(self, employee_id: str) -> list:
        """Return projects the employee is involved in."""
        with self._connect() as conn, conn.cursor() as cur:
            if self._is_dump_schema:
                cur.execute(
                    """
                    SELECT ep.employee_id::text, ep.project_id::text,
                           ep.role::text, ep.allocation_percent,
                           ep.start_date, ep.end_date,
                           p.name as project_name, p.status::text as project_status
                    FROM employee_projects ep
                    JOIN projects p ON ep.project_id = p.id
                    WHERE ep.employee_id = %s::bigint
                    ORDER BY p.name
                    """,
                    (employee_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT ep.employee_id, ep.project_id, ep.role, ep.allocation_percent,
                           ep.start_date, ep.end_date,
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
                    "project_id": str(r[1]), "role": str(r[2]),
                    "allocation_percent": r[3],
                    "project_name": str(r[6]), "project_status": str(r[7]),
                }
                for r in cur.fetchall()
            ]

    def get_goal_history_stats(self, employee_id: str) -> dict:
        """Return aggregated goal history: how many goals approved/rejected/drafted."""
        with self._connect() as conn, conn.cursor() as cur:
            if self._is_dump_schema:
                cur.execute(
                    "SELECT status::text, COUNT(*) FROM goals "
                    "WHERE employee_id = %s::bigint GROUP BY status",
                    (employee_id,),
                )
            else:
                cur.execute(
                    "SELECT status, COUNT(*) FROM goals WHERE employee_id = %s GROUP BY status",
                    (employee_id,),
                )
            return {str(k): int(v) for k, v in cur.fetchall()}

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
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")  # noqa: S608
            return cur.fetchone()[0]

    def has_dump_data(self) -> bool:
        """Check if the database has data from the organizer's dump (>50 employees)."""
        try:
            return self.count_table_rows("employees") > 50
        except Exception:
            return False
