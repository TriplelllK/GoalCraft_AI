#!/bin/bash
# ── GoalCraft AI: PostgreSQL dump restore script ─────────────────────
# This script restores the hackathon PGDMP-format dump (§4.2)
# into the database created by docker-compose.
# It runs automatically as a Docker entrypoint init script.
set -e

DUMP_FILE="/data/mock_smart_1.sql"

if [ -f "$DUMP_FILE" ]; then
    echo "=== [GoalCraft AI] Restoring hackathon dump (§4.2) ==="
    echo "    File: $DUMP_FILE"
    echo "    Database: $POSTGRES_DB"

    # pg_restore for custom-format dumps (.sql with PGDMP header)
    pg_restore \
        --no-owner \
        --no-privileges \
        --role="$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        "$DUMP_FILE" 2>&1 || echo "    ⚠ pg_restore completed with warnings (normal)"

    echo "=== [GoalCraft AI] Dump restoration complete ==="

    # Verify key tables
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
        SELECT 'departments' AS tbl, COUNT(*) FROM departments
        UNION ALL SELECT 'employees', COUNT(*) FROM employees
        UNION ALL SELECT 'goals', COUNT(*) FROM goals
        UNION ALL SELECT 'documents', COUNT(*) FROM documents;
    " 2>/dev/null || true
else
    echo "=== [GoalCraft AI] No dump file found at $DUMP_FILE ==="
    echo "    Running in demo mode with synthetic data."
fi
