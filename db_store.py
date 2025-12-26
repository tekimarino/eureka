"""PostgreSQL-backed JSON store for the app.

This app was originally file-based (data/*.json). On platforms like DigitalOcean App Platform,
local disk is ephemeral across deployments. To prevent data loss, we store each dataset inside
PostgreSQL (DO Managed DB) using a single JSONB table: public.kv_store.

Schema (compatible with the existing kv_store you already used):
  - k (text primary key)
  - v (jsonb)
  - updated_at (timestamptz)

Each former JSON file is stored under a key (e.g. users.json -> "users").
"""

from __future__ import annotations

import os
from typing import Any, Optional

import psycopg2
from psycopg2.extras import Json


def _dsn() -> Optional[str]:
    return os.getenv("DATABASE_URL")


def enabled() -> bool:
    return bool(_dsn())


def connect():
    """Create a new DB connection."""
    dsn = _dsn()
    if not dsn:
        raise RuntimeError("DATABASE_URL is not set")

    # DO Managed DB typically requires SSL.
    kwargs: dict[str, Any] = {
        "connect_timeout": int(os.getenv("PGCONNECT_TIMEOUT", "8")),
    }
    sslmode = os.getenv("PGSSLMODE")
    if sslmode:
        kwargs["sslmode"] = sslmode
    sslrootcert = os.getenv("PGSSLROOTCERT")
    if sslrootcert:
        kwargs["sslrootcert"] = sslrootcert

    return psycopg2.connect(dsn, **kwargs)


def ensure_schema() -> None:
    """Ensure kv_store exists. If the DB user has no CREATE privilege, this will raise."""
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS public.kv_store (
                  k TEXT PRIMARY KEY,
                  v JSONB NOT NULL,
                  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS kv_store_updated_at_idx
                ON public.kv_store (updated_at);
                """
            )
        conn.commit()


def get(key: str, default: Any = None) -> Any:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT v FROM public.kv_store WHERE k = %s", (key,))
            row = cur.fetchone()
            if not row:
                return default
            return row[0]


def set(key: str, value: Any) -> None:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.kv_store (k, v, updated_at)
                VALUES (%s, %s, now())
                ON CONFLICT (k)
                DO UPDATE SET v = EXCLUDED.v, updated_at = now();
                """,
                (key, Json(value)),
            )
        conn.commit()


def delete(key: str) -> None:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM public.kv_store WHERE k = %s", (key,))
        conn.commit()


def keys() -> list[str]:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT k FROM public.kv_store ORDER BY k")
            return [r[0] for r in cur.fetchall()]
