# Hotfix: add db_enabled alias in db_store.py (Windows PowerShell)
# Usage: from your project folder:  powershell -ExecutionPolicy Bypass -File .\apply_hotfix.ps1

$ErrorActionPreference = "Stop"

$target = Join-Path (Get-Location) "db_store.py"
if (!(Test-Path $target)) {
  Write-Host "❌ db_store.py not found in current folder: $(Get-Location)" -ForegroundColor Red
  exit 1
}

$content = Get-Content -Raw -Encoding UTF8 $target

# Already fixed?
if ($content -match "(?m)^\s*db_enabled\s*=") {
  Write-Host "✅ db_enabled already present. Nothing to do."
  exit 0
}

# Decide which internal flag exists
$aliasLine = $null
if ($content -match "(?m)^\s*_enabled\s*=") {
  $aliasLine = "db_enabled = _enabled  # public alias expected by app.py"
} elseif ($content -match "(?m)^\s*enabled\s*=") {
  $aliasLine = "db_enabled = enabled  # public alias expected by app.py"
} else {
  # fallback: define db_enabled from env
  $aliasLine = "db_enabled = bool(__import__('os').environ.get('DATABASE_URL'))  # fallback"
}

# Insert after the first occurrence of the internal flag (or after imports if none)
$lines = $content -split "`n", 0, "SimpleMatch"
$inserted = $false

for ($i=0; $i -lt $lines.Length; $i++) {
  if (!$inserted -and ($lines[$i] -match "^\s*_enabled\s*=" -or $lines[$i] -match "^\s*enabled\s*=")) {
    # Insert right after this line
    $newLines = @()
    $newLines += $lines[0..$i]
    $newLines += $aliasLine
    if ($i+1 -lt $lines.Length) { $newLines += $lines[($i+1)..($lines.Length-1)] }
    $lines = $newLines
    $inserted = $true
    break
  }
}

if (!$inserted) {
  # insert after last import line
  $lastImport = -1
  for ($i=0; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -match "^\s*(import|from)\s+") { $lastImport = $i }
  }
  if ($lastImport -ge 0) {
    $newLines = @()
    $newLines += $lines[0..$lastImport]
    $newLines += ""
    $newLines += $aliasLine
    if ($lastImport+1 -lt $lines.Length) { $newLines += $lines[($lastImport+1)..($lines.Length-1)] }
    $lines = $newLines
  } else {
    $lines = @($aliasLine) + $lines
  }
}

# Backup
$bak = "$target.bak"
Copy-Item $target $bak -Force

# Write back
($lines -join "`n") | Set-Content -Encoding UTF8 $target

Write-Host "✅ Hotfix applied: added db_enabled. Backup saved to db_store.py.bak" -ForegroundColor Green
