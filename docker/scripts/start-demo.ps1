# Inicia el demo completo de Cooperativa Financiera
$dockerDir = $PSScriptRoot | Split-Path -Parent
Set-Location $dockerDir

Write-Host ""
Write-Host "=== Cooperativa Financiera - Inicio Demo ===" -ForegroundColor Cyan

docker rm -f traefik banca-test cajas-test dash-test 2>&1 | Out-Null

$ErrorActionPreference = "Stop"

Write-Host "Levantando stack Docker (puede tardar varios minutos la primera vez)..." -ForegroundColor Yellow
docker compose -f docker-compose.yml -f docker-compose.app.yml -f docker-compose.dev.yml up -d --build

Write-Host "Esperando servicios..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host "Aplicando migraciones..." -ForegroundColor Yellow
& "$PSScriptRoot\apply-migrations.ps1"

Write-Host "Verificando salud..." -ForegroundColor Yellow
& "$PSScriptRoot\healthcheck-app.ps1"

Write-Host ""
Write-Host "=== Demo listo ===" -ForegroundColor Green
Write-Host "Portal:    http://localhost/"
Write-Host "Banca Web: http://localhost/web/  (DNI 45678901 / PIN 8901)"
Write-Host "Dashboard: http://localhost/dashboard/  (auditor / Coop2026!)"
Write-Host ""
Write-Host "Abra Chrome F12 Network antes de iniciar sesion" -ForegroundColor Cyan
Write-Host ""

Start-Process chrome.exe -ArgumentList "http://localhost/"
