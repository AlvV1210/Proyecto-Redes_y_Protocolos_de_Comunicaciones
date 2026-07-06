Write-Host "=== Healthcheck Capa Aplicacion PC3 ===" -ForegroundColor Cyan

function Test-Url($name, $url) {
    try {
        $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5
        if ($r.StatusCode -eq 200) { Write-Host "[OK] $name" -ForegroundColor Green; return $true }
    } catch {}
    Write-Host "[FAIL] $name ($url)" -ForegroundColor Red
    return $false
}

Test-Url "Nginx Gateway" "http://localhost/"
Test-Url "Auth Health" "http://localhost/api/v1/auth/health"
Test-Url "Banca Web (gateway)" "http://localhost/web/"
Test-Url "Banca Web (directo)" "http://localhost:8888/web/"
Test-Url "Cajas" "http://localhost/cajas/"
Test-Url "Dashboard" "http://localhost/dashboard/"

Write-Host ""
Write-Host "Login socio (POST):" -ForegroundColor Cyan
try {
    $body = '{"dni":"45678901","pin":"8901"}'
    $r = Invoke-RestMethod -Uri "http://localhost/api/v1/auth/socio/login" -Method POST -ContentType "application/json" -Body $body
    if ($r.access_token) { Write-Host "[OK] Login socio DNI 45678901" -ForegroundColor Green }
} catch {
    Write-Host "[FAIL] Login socio - ejecute: .\scripts\apply-migrations.ps1" -ForegroundColor Yellow
}
