#!/usr/bin/env bash
# Healthcheck capa de aplicación PC3
set -euo pipefail

echo "=== Healthcheck Capa Aplicación PC3 ==="

check() {
  local name="$1" url="$2"
  if curl -sf "$url" > /dev/null 2>&1; then
    echo "[OK] $name"
  else
    echo "[FAIL] $name ($url)"
    return 1
  fi
}

check "Gateway Auth" "http://localhost:8000/health" || check "Gateway Auth (traefik)" "http://localhost/api/v1/auth/health" || true
check "Cuentas SVC" "http://localhost:8001/health" || true
check "Prestamos SVC" "http://localhost:8002/health" || true
check "Auditoria SVC" "http://localhost:8003/health" || true
check "Sync SVC" "http://localhost:8004/health" || true
check "Traefik" "http://localhost:80" || true
check "Banca Web" "http://localhost/web/" || true
check "Cajas" "http://localhost/cajas/" || true
check "Dashboard SBS" "http://localhost/dashboard/" || true

echo ""
echo "=== Login de prueba (empleado) ==="
RESP=$(curl -sf -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"cajero.lima","password":"Coop2026!"}' 2>/dev/null || echo "")
if echo "$RESP" | grep -q access_token; then
  echo "[OK] Login empleado cajero.lima"
else
  echo "[WARN] Login empleado no verificado (¿stack completo arriba?)"
fi

echo ""
echo "=== Login de prueba (socio) ==="
RESP2=$(curl -sf -X POST http://localhost/api/v1/auth/socio/login \
  -H "Content-Type: application/json" \
  -d '{"dni":"45678901","pin":"8901"}' 2>/dev/null || echo "")
if echo "$RESP2" | grep -q access_token; then
  echo "[OK] Login socio DNI 45678901"
else
  echo "[WARN] Login socio no verificado"
fi

echo ""
echo "Healthcheck aplicación completado."
