# Recense PG17 (Flask + PostgreSQL 17)

Objectif: version "source of truth" PostgreSQL (aucune donnée métier en fichiers JSON).
Compatible DigitalOcean App Platform + Managed PostgreSQL 17.

## 1) Variables d'environnement (obligatoires)
- `DATABASE_URL` : URL PostgreSQL (format: `postgresql://user:pass@host:port/dbname?sslmode=require`)
- `SECRET_KEY` : secret Flask
- `JWT_SECRET_KEY` : secret JWT (peut être différent)

## 2) Lancer en local
```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt

# PowerShell (exemples)
$env:DATABASE_URL="postgresql://..."
$env:SECRET_KEY="change-me"
$env:JWT_SECRET_KEY="change-me-too"

flask --app manage.py db upgrade
flask --app manage.py create-admin --username admin --phone 0000000000 --password admin123

flask --app manage.py run --host 0.0.0.0 --port 5000
```

Endpoints:
- `GET /health`
- `POST /auth/login`  (json: {"username":"admin","password":"admin123"})
- `GET /auth/me` avec `Authorization: Bearer <token>`
- `GET /zones` (token)
- `GET /records?zone_id=...` (token)

## 3) Déploiement DigitalOcean (App Platform)
**Run command recommandé** (migrations avant gunicorn):
```sh
sh -c "flask --app manage.py db upgrade && gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120"
```

Variables d'environnement (Runtime):
- `DATABASE_URL`
- `SECRET_KEY`
- `JWT_SECRET_KEY`

## 4) Important
Sur DO App Platform, le disque de ton conteneur est **éphémère**: tout ce qui est écrit en fichiers (JSON, sqlite, etc.)
peut disparaître à chaque déploiement. Donc: **DB ou stockage externe** (Spaces) uniquement.
