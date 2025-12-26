#!/usr/bin/env bash
# Hotfix: add db_enabled alias in db_store.py (Linux/macOS)
# Usage: chmod +x apply_hotfix.sh && ./apply_hotfix.sh

set -euo pipefail

target="./db_store.py"
if [[ ! -f "$target" ]]; then
  echo "❌ db_store.py not found in current folder: $(pwd)"
  exit 1
fi

if grep -Eq '^[[:space:]]*db_enabled[[:space:]]*=' "$target"; then
  echo "✅ db_enabled already present. Nothing to do."
  exit 0
fi

bak="${target}.bak"
cp "$target" "$bak"

if grep -Eq '^[[:space:]]*_enabled[[:space:]]*=' "$target"; then
  # insert after first _enabled=
  awk '
    BEGIN{done=0}
    {print}
    (!done && $0 ~ /^[[:space:]]*_enabled[[:space:]]*=/){
      print "db_enabled = _enabled  # public alias expected by app.py"
      done=1
    }
  ' "$bak" > "$target"
elif grep -Eq '^[[:space:]]*enabled[[:space:]]*=' "$target"; then
  awk '
    BEGIN{done=0}
    {print}
    (!done && $0 ~ /^[[:space:]]*enabled[[:space:]]*=/){
      print "db_enabled = enabled  # public alias expected by app.py"
      done=1
    }
  ' "$bak" > "$target"
else
  # insert after imports
  awk '
    BEGIN{inserted=0}
    {print}
    (!inserted && $0 !~ /^[[:space:]]*(import|from)[[:space:]]+/ && prev_import==1){
      print "db_enabled = bool(__import__(\"os\").environ.get(\"DATABASE_URL\"))  # fallback"
      inserted=1
    }
    {prev_import=($0 ~ /^[[:space:]]*(import|from)[[:space:]]+/)}
  ' "$bak" > "$target"
fi

echo "✅ Hotfix applied. Backup saved to db_store.py.bak"
