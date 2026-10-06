# One-command local database setup for IngredientIQ (Windows PowerShell).
#
#   .\scripts\setup_db.ps1                       # finds ingredientiq*.dump automatically
#   .\scripts\setup_db.ps1 -Dump D:\x\ingredientiq.dump
#   .\scripts\setup_db.ps1 -Force                # wipe and re-restore even if data exists
#
# What it does: starts Postgres in Docker, restores the shared dump (if the
# database is empty), applies the SQL migrations, prints row counts.
# Needs: Docker Desktop running. No Postgres install or password needed.
param(
    [string]$Dump = "",
    [switch]$Force
)

# "Continue", not "Stop": docker prints progress on stderr, which PowerShell 5
# would otherwise treat as a fatal error. We check $LASTEXITCODE ourselves.
$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)

function Run-Psql($sql) {
    docker exec ingredientiq-db psql -U postgres -d ingredientiq -At -c $sql 2>$null
}

# 1. .env (the defaults in .env.example match docker-compose.yml)
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example"
}

# 2. Start Postgres and wait until it is healthy
Write-Host "Starting Postgres (Docker)..."
# --no-recreate: never restart a database that is already running.
docker compose up -d --wait --no-recreate
if ($LASTEXITCODE -ne 0) { throw "docker compose failed - is Docker Desktop running?" }

# 3. Restore the dump unless the data is already there
$existing = 0
$n = Run-Psql "SELECT count(*) FROM products"   # fails quietly if the table does not exist yet
if ($n -match '^\d+$') { $existing = [int]$n }

if ($existing -gt 0 -and -not $Force) {
    Write-Host "Database already has $existing products - skipping restore (use -Force to redo)."
} else {
    if (-not $Dump) {
        $found = Get-ChildItem -Recurse -Filter "ingredientiq*.dump" -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch "node_modules" } |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if (-not $found) { throw "No ingredientiq*.dump found. Download it from the team Drive and pass -Dump <path>." }
        $Dump = $found.FullName
    }
    Write-Host "Restoring $Dump (this takes a few minutes)..."
    docker cp $Dump ingredientiq-db:/tmp/ingredientiq.dump
    $clean = @()
    if ($Force) { $clean = @("--clean", "--if-exists") }
    docker exec ingredientiq-db pg_restore -U postgres -d ingredientiq -j 4 --no-owner @clean /tmp/ingredientiq.dump
    if ($LASTEXITCODE -ne 0) { Write-Warning "pg_restore reported warnings/errors - check the counts below." }
    docker exec ingredientiq-db rm -f /tmp/ingredientiq.dump
}

# 4. Migrations that are safe to re-run (CREATE ... IF NOT EXISTS)
Get-Content sql\003_review_signals.sql -Raw | docker exec -i ingredientiq-db psql -U postgres -d ingredientiq -q -v ON_ERROR_STOP=1

# 5. Show what we have
Write-Host ""
Write-Host "Row counts:"
foreach ($t in "products", "ingredients", "product_ingredients", "ingredient_knowledge",
               "product_functional_profiles", "reviews", "product_review_summary", "product_review_signals") {
    "{0,-30} {1,10}" -f $t, (Run-Psql "SELECT count(*) FROM $t")
}
Write-Host ""
Write-Host "Done. Next: python -m venv .venv; .venv\Scripts\pip install -r requirements.txt"
