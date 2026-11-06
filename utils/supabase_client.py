"""
Eco-Tide: Supabase Cloud Database Client
Provides an enterprise-ready backend integration with Supabase PostgreSQL for:
  1. Community Flood Incident Reports (community_reports)
  2. Community AI Chat & Citizen Dialogue (chat_messages)
  3. Real-Time Flood Risk Alert Logging (alert_history)

Backend-curated: Uses direct PostgreSQL connection pooler (port 6543) via psycopg2
with automatic credential detection from .streamlit/secrets.toml and environment variables,
plus seamless local JSON cache fallback.
"""

import os
import json
import time
from datetime import datetime, timezone
from contextlib import contextmanager
import toml
import psycopg2
from psycopg2.extras import RealDictCursor

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS_DIR = os.path.join(BASE_DIR, ".streamlit")
SECRETS_FILE = os.path.join(SECRETS_DIR, "secrets.toml")
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
LOCAL_REPORTS_FILE = os.path.join(DATA_DIR, "community_reports_local.json")
LOCAL_CHAT_FILE = os.path.join(DATA_DIR, "chat_messages_local.json")
LOCAL_ALERTS_FILE = os.path.join(DATA_DIR, "alert_history_local.json")

# Table names
TABLE_REPORTS = "community_reports"
TABLE_CHAT = "chat_messages"
TABLE_ALERTS = "alert_history"

# Global connectivity cache (TTL = 30s)
_connection_status_cache = {"connected": None, "timestamp": 0.0, "message": ""}


# ── Credential Resolution ─────────────────────────────────────────────────────

def get_database_url() -> str:
    """Retrieve full PostgreSQL connection string from secrets or environment."""
    # 1. Environment variable
    db_url = os.environ.get("DATABASE_URL", "").strip()
    if db_url:
        return db_url

    # 2. Streamlit secrets (if available in runtime)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"].strip()
    except Exception:
        pass

    # 3. Read .streamlit/secrets.toml directly from disk
    if os.path.exists(SECRETS_FILE):
        try:
            with open(SECRETS_FILE, "r", encoding="utf-8") as f:
                cfg = toml.load(f)
                if "DATABASE_URL" in cfg:
                    return str(cfg["DATABASE_URL"]).strip()
        except Exception:
            pass

    # 4. Fallback: empty if not configured
    return ""


def get_pg_params() -> dict:
    """Retrieve individual PostgreSQL connection parameters."""
    params = {
        "host": os.environ.get("PGHOST", "aws-1-eu-central-1.pooler.supabase.com"),
        "port": int(os.environ.get("PGPORT", 6543)),
        "dbname": os.environ.get("PGDATABASE", "postgres"),
        "user": os.environ.get("PGUSER", "postgres.dzigelcqcdaxhktbxtnv"),
        "password": os.environ.get("PGPASSWORD", ""),
        "sslmode": "require",
        "connect_timeout": 5,
    }

    # 1. Check Streamlit runtime secrets
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "postgres" in st.secrets:
            for k in ["host", "port", "dbname", "user", "password", "sslmode"]:
                if k in st.secrets["postgres"]:
                    val = st.secrets["postgres"][k]
                    params[k] = int(val) if k == "port" else str(val)
    except Exception:
        pass

    # 2. Check secrets.toml for [postgres] block
    if os.path.exists(SECRETS_FILE):
        try:
            with open(SECRETS_FILE, "r", encoding="utf-8") as f:
                cfg = toml.load(f)
                pg_sec = cfg.get("postgres", {})
                if pg_sec:
                    for k in ["host", "port", "dbname", "user", "password", "sslmode"]:
                        if k in pg_sec:
                            val = pg_sec[k]
                            params[k] = int(val) if k == "port" else str(val)
        except Exception:
            pass

    return params


def get_credentials() -> tuple[str, str]:
    """Retrieve Supabase URL and Key (compatibility helper)."""
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_ANON_KEY", "") or os.environ.get("SUPABASE_KEY", "")

    if not url or not key:
        if os.path.exists(SECRETS_FILE):
            try:
                with open(SECRETS_FILE, "r", encoding="utf-8") as f:
                    cfg = toml.load(f)
                    url = url or cfg.get("SUPABASE_URL", "")
                    key = key or cfg.get("SUPABASE_ANON_KEY", "") or cfg.get("SUPABASE_KEY", "")
            except Exception:
                pass

    if not url:
        url = "https://dzigelcqcdaxhktbxtnv.supabase.co"

    return url.strip(), key.strip()


def save_credentials(url: str, key: str) -> tuple[bool, str]:
    """Persist Supabase credentials to secrets.toml and environment."""
    url = url.strip()
    key = key.strip()

    os.environ["SUPABASE_URL"] = url
    os.environ["SUPABASE_ANON_KEY"] = key

    try:
        os.makedirs(SECRETS_DIR, exist_ok=True)
        secrets_data = {}
        if os.path.exists(SECRETS_FILE):
            try:
                with open(SECRETS_FILE, "r", encoding="utf-8") as f:
                    secrets_data = toml.load(f)
            except Exception:
                secrets_data = {}

        secrets_data["SUPABASE_URL"] = url
        secrets_data["SUPABASE_ANON_KEY"] = key

        with open(SECRETS_FILE, "w", encoding="utf-8") as f:
            toml.dump(secrets_data, f)
    except Exception as e:
        return False, f"Could not write to secrets.toml: {e}"

    ok, msg = check_connection()
    if ok:
        return True, "✅ Successfully connected to Supabase and saved credentials!"
    return False, f"Saved credentials, but test failed: {msg}"


# ── Database Connection Context Manager ───────────────────────────────────────

@contextmanager
def get_db_cursor(commit: bool = False):
    """
    Yields a psycopg2 cursor with RealDictCursor factory.
    Automatically handles commit and closure with timeout protection.
    Supports connection via DATABASE_URL or individual parameters.
    """
    conn = None
    try:
        db_url = get_database_url()
        params = get_pg_params()
        if db_url and not params.get("password"):
            conn = psycopg2.connect(dsn=db_url, connect_timeout=5)
        elif params.get("password"):
            conn = psycopg2.connect(**params)
        elif db_url:
            conn = psycopg2.connect(dsn=db_url, connect_timeout=5)
        else:
            raise ValueError("No database credentials configured.")
        if commit:
            conn.autocommit = True
        cur = conn.cursor(cursor_factory=RealDictCursor)
        yield cur
        if commit and not conn.autocommit:
            conn.commit()
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def is_connected() -> bool:
    """Return True if live Supabase PostgreSQL connection is active."""
    global _connection_status_cache
    now = time.time()
    if _connection_status_cache["connected"] is not None and (now - _connection_status_cache["timestamp"] < 30.0):
        return bool(_connection_status_cache["connected"])

    status, msg = check_connection()
    _connection_status_cache["connected"] = status
    _connection_status_cache["timestamp"] = now
    _connection_status_cache["message"] = msg
    return status


def check_connection() -> tuple[bool, str]:
    """
    Test live connectivity by attempting a minimal query against PostgreSQL.
    Returns (status: bool, message: str).
    """
    try:
        with get_db_cursor(commit=False) as cur:
            cur.execute("SELECT 1;")
            cur.fetchone()
        return True, "Connected to Supabase PostgreSQL (aws-1-eu-central-1.pooler.supabase.com:6543)"
    except Exception as e:
        return False, f"Database connection error: {e}"


def get_client():
    """Compatibility method returning REST client if supabase package is present."""
    url, key = get_credentials()
    if not url or not key:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception:
        return None


# ── Local File Persistence Helpers ────────────────────────────────────────────

def _load_local_json(file_path: str) -> list:
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _save_local_json(file_path: str, data: list):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    except Exception:
        pass


# ── 1. Community Flood Incident Reports ───────────────────────────────────────

def fetch_community_reports(limit: int = 50) -> list:
    """
    Fetch the most recent community flood incident reports.
    Queries Supabase PostgreSQL first; seamlessly falls back to local JSON cache.
    """
    try:
        with get_db_cursor(commit=False) as cur:
            cur.execute("""
                SELECT id, lga, reporter, severity, water_cm, msg, status,
                       lat, lon, accuracy_m, created_at, time
                FROM public.community_reports
                ORDER BY created_at DESC
                LIMIT %s;
            """, (limit,))
            rows = cur.fetchall()
            if rows:
                serialized = []
                for r in rows:
                    item = dict(r)
                    if isinstance(item.get("created_at"), datetime):
                        item["created_at"] = item["created_at"].isoformat()
                    serialized.append(item)
                _save_local_json(LOCAL_REPORTS_FILE, serialized)
                return serialized
    except Exception:
        pass

    return _load_local_json(LOCAL_REPORTS_FILE)


def submit_community_report(report: dict) -> tuple[bool, str]:
    """
    Submit a citizen flood incident report.
    Persists to Supabase PostgreSQL cloud and caches locally.
    """
    now_str = datetime.now(timezone.utc).isoformat()

    payload = {
        "lga":        report.get("lga", "Unknown"),
        "reporter":   report.get("reporter", "Anonymous Resident"),
        "severity":   report.get("severity", "Low"),
        "water_cm":   str(report.get("water_cm", "0 cm")),
        "msg":        report.get("msg", ""),
        "status":     report.get("status", "Community Broadcasted"),
        "created_at": now_str,
        "time":       report.get("time", "Just now"),
        "lat":        round(float(report["lat"]), 6) if report.get("lat") is not None else None,
        "lon":        round(float(report["lon"]), 6) if report.get("lon") is not None else None,
        "accuracy_m": report.get("accuracy_m"),
    }

    # Save to local cache first
    existing = _load_local_json(LOCAL_REPORTS_FILE)
    existing.insert(0, payload)
    if len(existing) > 100:
        existing = existing[:100]
    _save_local_json(LOCAL_REPORTS_FILE, existing)

    # Cloud Supabase PostgreSQL insert
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO public.community_reports
                    (lga, reporter, severity, water_cm, msg, status, lat, lon, accuracy_m, created_at, time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                payload["lga"],
                payload["reporter"],
                payload["severity"],
                payload["water_cm"],
                payload["msg"],
                payload["status"],
                payload["lat"],
                payload["lon"],
                payload["accuracy_m"],
                payload["created_at"],
                payload["time"]
            ))
            cur.fetchone()
        return True, "✅ Incident report broadcasted and synced to Supabase Cloud Database!"
    except Exception as e:
        return True, f"✅ Incident report saved locally (Cloud sync notice: {e})"


# ── 2. AI Community Chat Message Persistence ──────────────────────────────────

def fetch_chat_messages(limit: int = 50, language: str = "en") -> list:
    """
    Fetch saved community chat message history from Supabase or local cache.
    """
    try:
        with get_db_cursor(commit=False) as cur:
            cur.execute("""
                SELECT id, role, content, language, created_at
                FROM public.chat_messages
                WHERE language = %s
                ORDER BY created_at ASC
                LIMIT %s;
            """, (language, limit))
            rows = cur.fetchall()
            if rows:
                serialized = []
                for r in rows:
                    item = dict(r)
                    if isinstance(item.get("created_at"), datetime):
                        item["created_at"] = item["created_at"].isoformat()
                    serialized.append(item)
                return serialized
    except Exception:
        pass

    return _load_local_json(LOCAL_CHAT_FILE)


def save_chat_message(role: str, content: str, language: str = "en") -> bool:
    """
    Save a chat message from user or AI assistant to Supabase and local cache.
    """
    now_str = datetime.now(timezone.utc).isoformat()

    record = {
        "role":       role,
        "content":    content,
        "language":   language,
        "created_at": now_str,
    }

    # Save to local cache
    existing = _load_local_json(LOCAL_CHAT_FILE)
    existing.append(record)
    if len(existing) > 100:
        existing = existing[-100:]
    _save_local_json(LOCAL_CHAT_FILE, existing)

    # Save to Supabase PostgreSQL
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO public.chat_messages (role, content, language, created_at)
                VALUES (%s, %s, %s, %s);
            """, (role, content, language, now_str))
        return True
    except Exception:
        return False


# ── 3. Flood Risk Alert Logging ───────────────────────────────────────────────

def log_risk_alert(zone_name: str, level: str, score: float, water_level_m: float):
    """Log an active warning or danger level alert event."""
    now_str = datetime.now(timezone.utc).isoformat()
    record = {
        "zone_name":     zone_name,
        "level":         level,
        "score":         round(float(score), 4),
        "water_level_m": round(float(water_level_m), 3),
        "created_at":    now_str,
    }

    # Save locally
    existing = _load_local_json(LOCAL_ALERTS_FILE)
    existing.insert(0, record)
    if len(existing) > 100:
        existing = existing[:100]
    _save_local_json(LOCAL_ALERTS_FILE, existing)

    # Save to Supabase PostgreSQL
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO public.alert_history (zone_name, level, score, water_level_m, created_at)
                VALUES (%s, %s, %s, %s, %s);
            """, (zone_name, level, record["score"], record["water_level_m"], now_str))
    except Exception:
        pass


# ── 4. Supabase SQL Setup Script Generator ────────────────────────────────────

def get_setup_sql() -> str:
    """Returns the ready-to-run PostgreSQL schema script for reference."""
    return """-- Eco-Tide Cloud Database Schema
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
