# Pruebas de conectividad y transferencia — arquitectura completa
# No afecta las interfaces de usuario (Banca Web / Dashboard)
$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "=== Simulacion Capa Presentacion y Arquitectura ===" -ForegroundColor Cyan
Write-Host ""

function Test-Endpoint($name, $url, $method = "GET") {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        if ($method -eq "POST") {
            $r = Invoke-RestMethod -Uri $url -Method POST -TimeoutSec 30
        } else {
            $r = Invoke-RestMethod -Uri $url -TimeoutSec 30
        }
        $sw.Stop()
        Write-Host "[OK] $name ($($sw.ElapsedMilliseconds)ms)" -ForegroundColor Green
        return $r
    } catch {
        $sw.Stop()
        Write-Host "[FAIL] $name - $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

Write-Host "--- Capa Presentacion (Servidor Web nginx) ---" -ForegroundColor Yellow
Test-Endpoint "Portal demo" "http://localhost/" | Out-Null
Test-Endpoint "Banca Web (sin modificar UI)" "http://localhost/web/" | Out-Null
Test-Endpoint "Dashboard (sin modificar UI)" "http://localhost/dashboard/" | Out-Null
Test-Endpoint "Lab simulacion" "http://localhost/lab/" | Out-Null

Write-Host ""
Write-Host "--- Prueba de conectividad (toda la arquitectura) ---" -ForegroundColor Yellow
$conn = Test-Endpoint "Diagnostico conectividad" "http://localhost/api/v1/sync/diagnostico/conectividad"
if ($conn) {
    Write-Host "  Nodos OK: $($conn.resumen.ok) / $($conn.resumen.total) ($($conn.resumen.porcentaje_ok)%)" -ForegroundColor Cyan
    foreach ($capa in @("presentacion", "aplicacion", "datos")) {
        Write-Host "  [$capa]" -ForegroundColor DarkGray
        foreach ($n in $conn.capas.$capa.nodos) {
            $color = if ($n.estado -eq "OK") { "Green" } else { "Red" }
            Write-Host "    $($n.nodo): $($n.estado) ($($n.latencia_ms)ms)" -ForegroundColor $color
        }
    }
}

Write-Host ""
Write-Host "--- Prueba de transferencia de datos (via servidor web) ---" -ForegroundColor Yellow
$xfer = Test-Endpoint "Transferencia datos" "http://localhost/api/v1/sync/diagnostico/transferencia?via_gateway=true" "POST"
if ($xfer) {
    Write-Host "  Pasos OK: $($xfer.resumen.pasos_ok) / $($xfer.resumen.pasos_total)" -ForegroundColor Cyan
    Write-Host "  Bytes HTTP: $($xfer.resumen.bytes_http_acumulados) | Latencia total: $($xfer.resumen.latencia_total_ms)ms" -ForegroundColor Cyan
    foreach ($p in $xfer.pasos) {
        $color = if ($p.estado -eq "OK") { "Green" } elseif ($p.estado -eq "ADVERTENCIA") { "Yellow" } else { "Red" }
        Write-Host "    [$($p.paso)] $($p.flujo): $($p.estado)" -ForegroundColor $color
    }
}

Write-Host ""
Write-Host "Abra http://localhost/lab/ en Chrome con F12 Network para ver las peticiones." -ForegroundColor Cyan
Write-Host ""
