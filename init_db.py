import sys
import os
import psycopg2

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.supabase_client import get_pg_params

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS public.community_reports (
    id BIGSERIAL PRIMARY KEY,
    lga TEXT NOT NULL,
    reporter TEXT DEFAULT 'Anonymous Resident',
    severity TEXT DEFAULT 'Low',
    water_cm TEXT DEFAULT '0 cm',
    msg TEXT NOT NULL,
    status TEXT DEFAULT 'Community Broadcasted',
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    accuracy_m DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    time TEXT DEFAULT 'Just now'
);

CREATE TABLE IF NOT EXISTS public.chat_messages (
    id BIGSERIAL PRIMARY KEY,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    language TEXT DEFAULT 'en',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.alert_history (
    id BIGSERIAL PRIMARY KEY,
    zone_name TEXT NOT NULL,
    level TEXT NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    water_level_m DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

def main():
    print("Connecting to Supabase PostgreSQL using backend secrets...")
    params = get_pg_params()
    conn = psycopg2.connect(**params)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    tables_before = [r[0] for r in cur.fetchall()]
    print("Existing tables:", tables_before)

    print("Verifying schema DDL...")
    cur.execute(CREATE_TABLES_SQL)

    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    tables_after = [r[0] for r in cur.fetchall()]
    print("Current tables in public schema:", tables_after)

    cur.close()
    conn.close()
    print("Database verification complete.")

if __name__ == '__main__':
    main()
