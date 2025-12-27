"""
db_store.py
Minimal, production-safe PostgreSQL KV store used by app.py.

Exports expected by app.py:
- db_enabled
- ensure_store_ready
- kv_get
- kv_set
- kv_delete
- kv_keys
"""

from __future__ import annotations

import json
import os
from typing import Any, Iterable, Optional, Tuple, List

import psycopg2
from psycopg2.extras import RealDictCursor


# ---------- Connection helpers ----------

def _dsn() -> Optional[str]:
    """
    Prefer DATABASE_URL (common on Heroku/DO). Fallback to discrete PG* vars.
    """
    url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or os.getenv("PGDATABASE_URL")
    if url:
        return url

    host = os.getenv("PGHOST")
    port = os.getenv("PGPORT", "5432")
    dbname = os.getenv("PGDATABASE") or os.getenv("PGDB") or os.getenv("DB_NAME")
    user = os.getenv("PGUSER") or os.getenv("DB_USER")
    password = os.getenv("PGPASSWORD") or os.getenv("DB_PASSWORD")

    if not (host and dbname and user and password):
        return None

    # Use keyword DSN; sslmode handled separately in _connect kwargs
    return f"host={host} port={port} dbname={dbname} user={user} password={password}"


def db_enabled() -> bool:
    """
    True if we have enough env vars to connect to PostgreSQL.
    """
    return _dsn() is not None

def _connect():
    dsn = _dsn()
    if not dsn:
        raise RuntimeError("PostgreSQL not configured (missing DATABASE_URL / PG* env vars).")

    # SSL defaults: require in managed DBs
    sslmode = os.getenv("PGSSLMODE", "require")
    kwargs = {"sslmode": sslmode}

    # Optional CA cert (DigitalOcean provides a CA bundle sometimes)
    rootcert = os.getenv("PGSSLROOTCERT")
    if rootcert:
        kwargs["sslrootcert"] = rootcert

    return psycopg2.connect(dsn, **kwargs)


# ---------- KV store API ----------

def ensure_store_ready() -> None:
    """
    Creates the kv_store table if it doesn't exist.
    Requires privileges on schema public (USAGE + CREATE) OR table already exists.
    """
    if not db_enabled():
        return

    sql = """
    CREATE TABLE IF NOT EXISTS public.kv_store (
        k TEXT PRIMARY KEY,
        v JSONB NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()


def kv_get(key: str, default: Any = None) -> Any:
    """
    Returns the JSON value for key or default if missing.
    """
    if not db_enabled():
        return default

    ensure_store_ready()

    with _connect() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT v FROM public.kv_store WHERE k=%s;", (key,))
            row = cur.fetchone()
            if not row:
                return default
            return row["v"]


def kv_set(key: str, value: Any) -> None:
    """
    Upserts key with JSON value.
    """
    if not db_enabled():
        raise RuntimeError("PostgreSQL not configured; cannot kv_set.")

    ensure_store_ready()

    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.kv_store (k, v, updated_at)
                VALUES (%s, %s::jsonb, NOW())
                ON CONFLICT (k)
                DO UPDATE SET v=EXCLUDED.v, updated_at=NOW();
                """,
                (key, json.dumps(value, ensure_ascii=False)),
            )
        conn.commit()


def kv_delete(key: str) -> None:
    if not db_enabled():
        return
    ensure_store_ready()
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM public.kv_store WHERE k=%s;", (key,))
        conn.commit()


def kv_keys(prefix: Optional[str] = None, limit: int = 2000) -> List[str]:
    """
    Lists keys, optionally filtered by prefix.
    """
    if not db_enabled():
        return []
    ensure_store_ready()

    if prefix:
        sql = "SELECT k FROM public.kv_store WHERE k LIKE %s ORDER BY updated_at DESC LIMIT %s;"
        params = (prefix + "%", limit)
    else:
        sql = "SELECT k FROM public.kv_store ORDER BY updated_at DESC LIMIT %s;"
        params = (limit,)

    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return [r[0] for r in cur.fetchall()]


# Backward-compatible aliases (in case some code imports old names)
enabled = db_enabled
