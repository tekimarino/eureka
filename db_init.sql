-- One-time PostgreSQL initialization for the Recensement app
--
-- Run this as the database admin user (e.g., doadmin on DigitalOcean Managed PostgreSQL).
-- Replace <APP_USER> with the database user used by your app (e.g., recense_user).

CREATE TABLE IF NOT EXISTS public.kv_store (
  k text PRIMARY KEY,
  v jsonb NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Optional index (useful for admin screens / troubleshooting)
CREATE INDEX IF NOT EXISTS kv_store_updated_at_idx ON public.kv_store (updated_at DESC);

-- Permissions
GRANT USAGE ON SCHEMA public TO <APP_USER>;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.kv_store TO <APP_USER>;
