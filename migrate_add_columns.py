"""One-time, idempotent schema migration for the DB-model consolidation fix.

Why this is needed: app/database.py's AnalysisSession/AnalysisLog models
changed (added `pdf_bytes`, `session_id`, `provider`, `report_type`; the old
`server_path` NOT NULL column on analysis_logs is no longer written by the
code). SQLAlchemy's create_all() (called by init_db() on every API startup)
only creates tables that don't exist yet — it never ALTERs a table that's
already there. Since your Postgres already has these tables from before
this fix, the new columns simply don't exist on disk yet, which is exactly
the `column analysis_sessions.pdf_bytes does not exist` error you're
seeing. This script brings the existing table in sync WITHOUT touching any
existing rows (users, saved sessions, logs all stay intact).

Run it once, from inside the `api` container (it already has DATABASE_URL
set and the sqlalchemy dependency installed):

    docker compose exec api python migrate_add_columns.py

Safe to run more than once — every statement is a no-op if already applied.

If you don't care about existing data (e.g. this is still a dev/test
database), the alternative is `python reset_db.py`, which drops and
recreates every table from scratch and creates a fresh admin account — but
that destroys any users/sessions/logs you already have. Use this script
instead if you want to keep them.
"""
from sqlalchemy import text

from app.database import engine

STATEMENTS = [
    # analysis_sessions.pdf_bytes — stores the original PDF so the
    # "Archive" screen can preview it. Added by the auth.py/database.py
    # model-consolidation fix.
    "ALTER TABLE analysis_sessions ADD COLUMN IF NOT EXISTS pdf_bytes BYTEA;",

    # analysis_logs — new columns used by the updated log_analysis() call
    # in app/routers/process.py.
    "ALTER TABLE analysis_logs ADD COLUMN IF NOT EXISTS session_id VARCHAR;",
    "ALTER TABLE analysis_logs ADD COLUMN IF NOT EXISTS provider VARCHAR;",
    "ALTER TABLE analysis_logs ADD COLUMN IF NOT EXISTS report_type VARCHAR;",

    # server_path used to be a required (NOT NULL) column on analysis_logs.
    # The current code never writes it, so every insert would otherwise
    # fail with a NOT NULL violation. Relax the constraint (guarded so this
    # is a no-op if the column has already been altered or doesn't exist).
    """
    DO $$
    BEGIN
      IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'analysis_logs' AND column_name = 'server_path'
      ) THEN
        ALTER TABLE analysis_logs ALTER COLUMN server_path DROP NOT NULL;
      END IF;
    END $$;
    """,
]


def main():
    with engine.begin() as conn:
        for stmt in STATEMENTS:
            print(f"→ {stmt.strip().splitlines()[0]}...")
            conn.execute(text(stmt))
    print("✅ Migration complete — existing data was not touched.")


if __name__ == "__main__":
    main()
