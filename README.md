# Recensement Électoral 2028 (Flask + PostgreSQL 17)

Application légère pour enregistrer des électeurs (via des agents recenseurs) et valider les données (via des superviseurs par zone).

## Fonctionnalités
- Comptes utilisateurs avec rôles : **admin**, **supervisor**, **agent**
- Gestion des **zones** (admin)
- Création de **superviseurs** (assignés à une zone) et d’**agents** (assignés à une zone + un superviseur)
- Saisie côté agent : **Nom, Prénoms, Date de naissance, Quartier, Téléphone**
- Validation côté superviseur : ajout du **Numéro d’électeur**, **Centre de vote** et **Bureau de vote** + statut (**Validé / Rejeté**)
- Stockage **100% PostgreSQL** (recommandé en production) via `public.kv_store` (JSONB) : aucune perte de données au redéploiement
- Mode local possible : stockage fichier (JSON) si `DATABASE_URL` n'est pas défini
- Admin : accès à la **liste des personnes recensées** avec recherche + filtres (zone, centre de vote)
- **SMS de masse** (admin) et **SMS de zone** (superviseur) via une file d’attente JSON : `data/sms_outbox.json` + campagnes `data/sms_campaigns.json`

## Comptes par défaut (à changer immédiatement)
- Admin : `admin` / `Admin2028@`
- Superviseur : `sup_adiaho` / `Sup2028@`
- Agent : `agent_01` / `Agent2028@`

> Important : modifiez ces mots de passe dès le démarrage (menu Admin > Utilisateurs).

## Installation (local)
1. Installer Python 3.10+.
2. Ouvrir un terminal dans le dossier du projet, puis :
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate

   pip install -r requirements.txt
   ```
3. Lancer (mode fichier par défaut) :
   ```bash
   python app.py
   ```
4. Ouvrir : http://127.0.0.1:5000

## Mode PostgreSQL (production / DigitalOcean)

L'application bascule automatiquement en **mode base de données** dès que la variable d'environnement `DATABASE_URL` est présente.

### Table utilisée
La persistance se fait dans **une seule table** compatible avec PostgreSQL 17 :

- `public.kv_store` : `(k TEXT PRIMARY KEY, v JSONB, updated_at TIMESTAMPTZ)`

Chaque dataset (users, zones, centres, registrations, settings, etc.) est stocké sous une clé (ex: `users`, `zones`, `centers`).

### Première initialisation (seed)
Au premier démarrage en DB mode, si une clé n'existe pas encore dans `kv_store`, l'app :
1) tente de la charger depuis le fichier correspondant dans `data/*.json` (s'il est présent dans le repo), sinon
2) crée une valeur par défaut.

## Sécurité (minimum vital)
- Changez la clé de session Flask :
  - Créez une variable d’environnement `SECRET_KEY` (forte et privée)
- En production, exécutez derrière un reverse proxy HTTPS (Nginx, Caddy, etc.)
- En production, faites des sauvegardes via **Admin > Backup** (export ZIP). En DB mode, il exporte un snapshot des données de la base.

## Déploiement simple (exemple)
- Utilisez un VPS (DigitalOcean, OVH, etc.)
- Installez Python + dépendances
- Lancez avec un serveur WSGI (ex. gunicorn) derrière Nginx, avec HTTPS

## Structure
- `app.py` : application Flask
- `templates/` : pages HTML
- `static/` : CSS/JS
- `data/` : fichiers JSON (seed + backups). En production, la donnée vit dans PostgreSQL.

## Déploiement (DigitalOcean App Platform)
- Ajoutez `DATABASE_URL` dans les variables d'environnement (connexion au PostgreSQL Managed DB)
- Commande d'exécution : `gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
- Python fixé via `.python-version` (évite les problèmes de compatibilité psycopg2)


## SMS (mode simulation par défaut)
Par défaut, l’application est en **mode DRY_RUN** : les SMS sont ajoutés à une file (`data/sms_outbox.json`) mais **aucun fournisseur n’est contacté**.

Pour brancher un fournisseur via une API HTTP JSON :
1. Ouvrez `data/sms_config.json`
2. Mettez `"mode": "http_json"`
3. Renseignez `http_json.url` (endpoint) et, si besoin, `http_json.token` (Bearer)
4. Cliquez sur **Traiter la file** (envois par lots, max `MAX_SMS_SEND_PER_REQUEST` par clic)

> Note : chaque fournisseur a son format. Ici, on envoie un JSON simple `{to, message, sender}` (configurable via `to_field`, `message_field`, `sender_field`).
