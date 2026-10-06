# Export the whole local database (including the review signals we computed)
# to ONE file you can send to a teammate. They run scripts\setup_db.ps1 -Dump <file>.
#
#   .\scripts\export_db.ps1                      # writes .\ingredientiq_full.dump
param([string]$Out = "ingredientiq_full.dump")

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

docker exec ingredientiq-db pg_dump -U postgres -d ingredientiq -Fc -f /tmp/export.dump
if ($LASTEXITCODE -ne 0) { throw "pg_dump failed - is the ingredientiq-db container running?" }
docker cp ingredientiq-db:/tmp/export.dump $Out
docker exec ingredientiq-db rm -f /tmp/export.dump
"{0}  ({1:N0} MB)" -f (Resolve-Path $Out), ((Get-Item $Out).Length / 1MB)
