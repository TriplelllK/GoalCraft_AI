#!/usr/bin/env python3
"""
Загрузка SQL-дампа организаторов хакатона в PostgreSQL.

Этот скрипт:
1. Подключается к PostgreSQL (из переменных окружения или docker-compose)
2. Загружает .sql дамп (custom format или plain SQL)
3. Проверяет что все 13 таблиц из §4.2 ТЗ доступны
4. Выводит статистику по загруженным данным

Использование:
    # Plain SQL файл:
    python scripts/load_dump.py path/to/dump.sql

    # С указанием параметров подключения:
    DATABASE_URL=postgresql://user:pass@host:5432/dbname python scripts/load_dump.py dump.sql

    # Через psql напрямую (рекомендуется для custom format):
    psql -U postgres -d hr_goal_ai -f dump.sql
    # Затем проверить:
    python scripts/load_dump.py --verify-only
"""

from __future__ import annotations

import os
import subprocess
import sys


def get_db_params() -> dict:
    """Get database connection parameters from environment."""
    url = os.getenv("DATABASE_URL", "")
    if url:
        return {"url": url}
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "dbname": os.getenv("POSTGRES_DB", "hr_goal_ai"),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    }


def _is_pgdmp(sql_path: str) -> bool:
    """Check if file is a PostgreSQL custom-format dump (PGDMP header)."""
    try:
        with open(sql_path, "rb") as f:
            return f.read(5) == b"PGDMP"
    except Exception:
        return False


def load_sql_file(sql_path: str, params: dict) -> bool:
    """Load a .sql file using pg_restore (PGDMP) or psql (plain SQL)."""
    if "url" in params:
        from urllib.parse import urlparse
        p = urlparse(params["url"])
        host = p.hostname or "localhost"
        port = str(p.port or 5432)
        user = p.username or "postgres"
        password = p.password or "postgres"
        dbname = p.path.lstrip("/") or "hr_goal_ai"
    else:
        host = params["host"]
        port = params["port"]
        user = params["user"]
        password = params["password"]
        dbname = params["dbname"]

    env = os.environ.copy()
    env["PGPASSWORD"] = password

    use_pg_restore = _is_pgdmp(sql_path)

    if use_pg_restore:
        cmd = [
            "pg_restore",
            "--no-owner",
            "--no-privileges",
            "-h", host,
            "-p", port,
            "-U", user,
            "-d", dbname,
            sql_path,
        ]
        tool_name = "pg_restore"
    else:
        cmd = [
            "psql",
            "-h", host,
            "-p", port,
            "-U", user,
            "-d", dbname,
            "-f", sql_path,
        ]
        tool_name = "psql"

    print(f"[*] Формат дампа: {'PGDMP (custom)' if use_pg_restore else 'Plain SQL'}")
    print(f"[*] Загрузка дампа: {sql_path}")
    print(f"[*] Команда: {tool_name} → {dbname}@{host}:{port}")

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )
        # pg_restore returns non-zero on warnings too, check stderr for real errors
        if result.returncode != 0:
            if use_pg_restore and "ERROR" not in result.stderr:
                print(f"[✓] Дамп загружен (pg_restore с предупреждениями — это нормально)")
                return True
            print(f"[!] Ошибка {tool_name} (код {result.returncode}):")
            print(result.stderr[:2000])
            return False
        print("[✓] Дамп успешно загружен")
        return True
    except FileNotFoundError:
        print(f"[!] {tool_name} не найден. Установите PostgreSQL client.")
        if use_pg_restore:
            print("    pg_restore поставляется вместе с PostgreSQL.")
        return False
    except subprocess.TimeoutExpired:
        print("[!] Таймаут загрузки дампа (300с)")
        return False


def verify_tables(params: dict) -> dict[str, int]:
    """Verify all 13 tables and count rows."""
    try:
        import psycopg
    except ImportError:
        print("[!] psycopg не установлен. pip install psycopg[binary]")
        return {}

    url = params.get("url") or (
        f"postgresql://{params['user']}:{params['password']}"
        f"@{params['host']}:{params['port']}/{params['dbname']}"
    )

    tables_expected = [
        "departments", "positions", "employees", "documents", "goals",
        "projects", "systems", "project_systems", "employee_projects",
        "goal_events", "goal_reviews", "kpi_catalog", "kpi_timeseries",
    ]

    stats: dict[str, int] = {}
    with psycopg.connect(url) as conn, conn.cursor() as cur:
        for table in tables_expected:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")  # noqa: S608
                count = cur.fetchone()[0]
                stats[table] = count
            except Exception as e:
                stats[table] = -1  # Table doesn't exist
                conn.rollback()

    return stats


def print_stats(stats: dict[str, int]) -> None:
    """Pretty-print table statistics."""
    tz_expected = {
        "departments": 8, "positions": 25, "employees": 450,
        "documents": 160, "goals": 9000,
        "projects": 34, "systems": 10, "project_systems": 65,
        "employee_projects": 886,
        "goal_events": 30789, "goal_reviews": 4305,
        "kpi_catalog": 13, "kpi_timeseries": 2112,
    }

    print("\n" + "=" * 60)
    print(f"{'Таблица':<22} {'Записей':>10} {'Ожидание ТЗ':>14} {'Статус':>8}")
    print("-" * 60)
    for table, count in stats.items():
        expected = tz_expected.get(table, "?")
        if count == -1:
            status = "❌ MISS"
        elif count == 0:
            status = "⚠️  EMPTY"
        elif count >= (expected if isinstance(expected, int) else 0):
            status = "✅ OK"
        else:
            status = "⚠️  LOW"
        print(f"{table:<22} {count:>10} {str(expected):>14} {status:>8}")
    print("=" * 60)

    total = sum(v for v in stats.values() if v > 0)
    missing = sum(1 for v in stats.values() if v == -1)
    empty = sum(1 for v in stats.values() if v == 0)
    print(f"\nВсего записей: {total:,}")
    if missing:
        print(f"⚠️  Отсутствуют таблицы: {missing}")
    if empty:
        print(f"⚠️  Пустые таблицы: {empty}")
    if not missing and not empty:
        print("✅ Все 13 таблиц из §4.2 ТЗ присутствуют и заполнены")


def main():
    params = get_db_params()
    verify_only = "--verify-only" in sys.argv

    if not verify_only:
        # Find .sql file argument
        sql_files = [arg for arg in sys.argv[1:] if arg.endswith(".sql")]
        if not sql_files:
            print("Использование:")
            print("  python scripts/load_dump.py path/to/dump.sql")
            print("  python scripts/load_dump.py --verify-only")
            print()
            print("Или загрузите дамп напрямую:")
            print("  psql -U postgres -d hr_goal_ai -f dump.sql")
            print("  python scripts/load_dump.py --verify-only")
            sys.exit(1)

        sql_path = sql_files[0]
        if not os.path.exists(sql_path):
            print(f"[!] Файл не найден: {sql_path}")
            sys.exit(1)

        if not load_sql_file(sql_path, params):
            print("[!] Загрузка не удалась. Попробуйте загрузить вручную через psql.")
            sys.exit(1)

    print("\n[*] Проверка таблиц...")
    stats = verify_tables(params)
    if stats:
        print_stats(stats)
    else:
        print("[!] Не удалось подключиться к БД для проверки")
        sys.exit(1)


if __name__ == "__main__":
    main()
