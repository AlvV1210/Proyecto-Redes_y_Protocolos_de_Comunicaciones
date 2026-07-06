# Aplicar migraciones de autenticación (socios + passwords)
# Uso: .\scripts\apply-migrations.ps1

$projectRoot = Resolve-Path "$PSScriptRoot\..\.."
Write-Host "Aplicando migraciones SQL..." -ForegroundColor Cyan

Get-Content "$projectRoot\database\05-socio-auth.sql" | docker exec -i core-db psql -U coop_admin -d core_bancario
Get-Content "$projectRoot\database\06-update-passwords.sql" | docker exec -i core-db psql -U coop_admin -d core_bancario

Write-Host "Migraciones aplicadas." -ForegroundColor Green
Write-Host "Probar login socio: DNI 45678901 / PIN 8901"
